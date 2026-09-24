{
  description = "nixarchy-menu -- a Raycast-style command palette Omarchy plugin, with Smart Match, voice, Codex and extensions";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Checks only: shell/Commons, shell/Ui and shell/plugins/menu/MenuModel.js
    # are the same tree Omarchy loads at runtime. Not a runtime dependency of
    # the plugin itself, and never nixarchy (that would be circular, since
    # nixarchy takes this repo as an input).
    omarchy = {
      url = "github:basecamp/omarchy/v4.0.4";
      flake = false;
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      omarchy,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAll = nixpkgs.lib.genAttrs systems;

      # The three model files nixarchy-menu's Smart Match needs, pinned to
      # the same Hugging Face revisions and digests as the (now deleted)
      # helpers/matching-start.py used to fetch at runtime.
      modelFile =
        pkgs: repo: rev: file: sha256:
        pkgs.fetchurl {
          url = "https://huggingface.co/${repo}/resolve/${rev}/${file}";
          inherit sha256;
        };
    in
    {
      packages = forAll (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          matching-engine = pkgs.rustPlatform.buildRustPackage {
            pname = "keystroke-matching";
            version = "0.1.0";
            src = ./matching/engine;
            cargoLock.lockFile = ./matching/engine/Cargo.lock;
            meta = with pkgs.lib; {
              description = "Resident local Model2Vec embeddings for nixarchy-menu Smart Match";
              license = licenses.mit;
              platforms = platforms.linux;
            };
          };

          # Shared by both models: identical revision and digest either way.
          tokenizer =
            modelFile pkgs "minishlab/potion-base-2M" "389b9f64be5aa4ae7a6bc6fe95ef20ce485ae5da"
              "tokenizer.json"
              "e67e803f624fb4d67dea1c730d06e1067e1b14d830e2c2202569e3ef0f70bb50";

          model-small = pkgs.runCommand "keystroke-model-small" { } ''
            mkdir -p "$out"
            cp ${
              modelFile pkgs "minishlab/potion-base-2M" "389b9f64be5aa4ae7a6bc6fe95ef20ce485ae5da" "config.json"
                "b2a89173391ca774c2d7323090a993a9a1553faa5b40eb37bb7cec6685fbea47"
            } "$out/config.json"
            cp ${tokenizer} "$out/tokenizer.json"
            cp ${
              modelFile pkgs "minishlab/potion-base-2M" "389b9f64be5aa4ae7a6bc6fe95ef20ce485ae5da"
                "model.safetensors"
                "f95ffde02ad06f63ae38eb9d400038cd5ccaf8411ec3cb650c6025113f96cbb8"
            } "$out/model.safetensors"
          '';

          model-large = pkgs.runCommand "keystroke-model-large" { } ''
            mkdir -p "$out"
            cp ${
              modelFile pkgs "minishlab/potion-base-8M" "bf8b056651a2c21b8d2565580b8569da283cab23" "config.json"
                "2a6ac0e9aaa356a68a5688070db78fc3a464fefe85d2f06a1905ce3718687553"
            } "$out/config.json"
            cp ${tokenizer} "$out/tokenizer.json"
            cp ${
              modelFile pkgs "minishlab/potion-base-8M" "bf8b056651a2c21b8d2565580b8569da283cab23"
                "model.safetensors"
                "f65d0f325faadc1e121c319e2faa41170d3fa07d8c89abd48ca5358d9a223de2"
            } "$out/model.safetensors"
          '';

          # A plain-copy runCommand, deliberately: omarchy-plugin-validate
          # refuses ANY symlink inside a plugin folder, so symlinkJoin, a
          # wrapped binary or a linkFarm all fail validation at rebuild time.
          plugin =
            pkgs.runCommand "nixarchy-menu"
              {
                meta = with pkgs.lib; {
                  description = "Omarchy menu plugin: command palette, Smart Match, voice, Codex and extensions";
                  homepage = "https://github.com/olafkfreund/nixarchy-menu";
                  license = licenses.mit;
                  platforms = platforms.linux;
                };
              }
              ''
                src=${self}
                mkdir -p "$out"
                cp "$src"/manifest.json "$src"/LICENSE "$out/"
                cp "$src"/*.qml "$out/"
                cp -r "$src"/core "$src"/providers "$src"/ui "$src"/voice "$src"/codex "$out/"
                cp -r "$src"/extensions "$out/"
                cp -r "$src"/helpers "$out/"
                mkdir -p "$out/matching"
                cp "$src"/matching/Session.qml "$src"/matching/descriptions.json "$src"/matching/description-keys.json "$out/matching/"
                cp -r "$src"/bin "$out/"

                chmod -R u+w "$out"

                rm -rf "$out"/extensions/*/tests
                find "$out" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
                find "$out" -name '*.pyc' -delete

                chmod +x "$out"/bin/* "$out"/helpers/*.sh "$out"/helpers/*.py

                substituteInPlace "$out/matching/Session.qml" \
                  --replace-fail '@matchingEngine@' '${matching-engine}/bin/keystroke-matching' \
                  --replace-fail '@modelSmall@' '${model-small}' \
                  --replace-fail '@modelLarge@' '${model-large}'
              '';
        in
        {
          inherit
            matching-engine
            model-small
            model-large
            plugin
            ;
          default = plugin;
        }
      );

      checks = forAll (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          inherit (self.packages.${system}) matching-engine model-small plugin;

          # One copy of the repo, shared by every check, with the MenuModel
          # import pointed at the pinned Omarchy tree instead of the runtime
          # path a real Omarchy install provides.
          checkSrc = pkgs.runCommand "nixarchy-menu-check-src" { } ''
            cp -r ${self} "$out"
            chmod -R u+w "$out"
            substituteInPlace "$out/providers/OmarchyMenu.qml" "$out/tests/tst_menumodel.qml" \
              --replace-fail 'file:///run/current-system/sw/share/omarchy' 'file://${omarchy}'
          '';

          engineCheckPython = pkgs.python3.withPackages (ps: [ ps.tokenizers ]);
        in
        {
          # The manifest is what omarchy-plugin-validate and the shell check
          # at load, so a typo here is a plugin that silently never appears.
          # The pacman/yay grep matches nixarchy's own validatedPlugins check
          # (modules/home.nix), since this plugin has to pass it too.
          plugin =
            pkgs.runCommand "nixarchy-menu-check-plugin"
              {
                nativeBuildInputs = [
                  pkgs.jq
                  pkgs.findutils
                  pkgs.gnugrep
                ];
              }
              ''
                jq -e '
                  .id == "nixarchy.menu"
                  and .omarchy.clonedFrom == "omarchy.menu"
                  and (.entryPoints.menu == "NixarchyMenu.qml")
                  and (.entryPoints.barWidget == "BarWidget.qml")
                ' ${plugin}/manifest.json > /dev/null
                test -f ${plugin}/NixarchyMenu.qml
                test -f ${plugin}/BarWidget.qml
                test -z "$(find ${plugin} -type l)"
                if grep -rE '@(matchingEngine|modelSmall|modelLarge)@' ${plugin} >&2; then
                  echo "unsubstituted placeholder left in the plugin output" >&2
                  exit 1
                fi
                hits=$(
                  find ${plugin} -type f \( -name '*.qml' -o -name '*.js' -o -name '*.sh' -o -name '*.bash' \) -print0 |
                    xargs -0 -r grep -nHE '\bpacman\b|\byay\b' |
                    grep -vE ':[0-9]+:[[:space:]]*(//|#)' || true
                )
                if [ -n "$hits" ]; then
                  echo "$hits" >&2
                  echo "nixarchy-menu would fail nixarchy's validatedPlugins check" >&2
                  exit 1
                fi
                touch $out
              '';

          qml-unit =
            pkgs.runCommand "nixarchy-menu-check-qml-unit"
              {
                nativeBuildInputs = [
                  pkgs.qt6.qtdeclarative
                  pkgs.qt6.qtbase
                  pkgs.python3
                ];
              }
              ''
                export HOME=$TMPDIR
                export OMARCHY_PATH=${omarchy}
                export QT_QPA_PLATFORM=offscreen
                export QT_QUICK_BACKEND=software
                export QML2_IMPORT_PATH=${pkgs.qt6.qtdeclarative}/lib/qt-6/qml
                export QT_PLUGIN_PATH=${pkgs.qt6.qtbase}/lib/qt-6/plugins
                (cd ${checkSrc}/tests && qmltestrunner -input .)
                python3 ${checkSrc}/tools/check_extensions.py
                touch $out
              '';

          lint =
            pkgs.runCommand "nixarchy-menu-check-lint"
              {
                nativeBuildInputs = [
                  pkgs.qt6.qtdeclarative
                  pkgs.ripgrep
                ];
              }
              ''
                export HOME=$TMPDIR
                export OMARCHY_PATH=${omarchy}
                bash ${checkSrc}/tests/lint.sh
                touch $out
              '';

          # The quickshell *_check.py palette and session checks, plus the
          # three extension palette checks, run sequentially. hotkeys_check
          # needs a live Hyprland (runs via `bin/nixarchy-menu test` on a host
          # instead); matching_engine_check and migrate_state_check are their
          # own checks below; matching_worker_check no longer exists;
          # tz_helper_check doesn't touch quickshell at all.
          quickshell =
            pkgs.runCommand "nixarchy-menu-check-quickshell"
              {
                nativeBuildInputs = [
                  pkgs.quickshell
                  pkgs.python3
                  pkgs.bash
                  pkgs.jq
                  pkgs.coreutils
                  pkgs.qt6.qtbase
                  pkgs.fd
                ];
              }
              ''
                export HOME=$TMPDIR
                export OMARCHY_PATH=${omarchy}
                export QT_QPA_PLATFORM=offscreen
                export QML2_IMPORT_PATH=${pkgs.qt6.qtdeclarative}/lib/qt-6/qml
                export QT_PLUGIN_PATH=${pkgs.qt6.qtbase}/lib/qt-6/plugins
                export XDG_RUNTIME_DIR=$TMPDIR/xdg-runtime
                mkdir -p "$XDG_RUNTIME_DIR"
                chmod 700 "$XDG_RUNTIME_DIR"
                cd ${checkSrc}
                for f in tests/palette_url_check.py \
                         tests/palette_motion_check.py \
                         tests/palette_currency_check.py \
                         tests/palette_matching_check.py \
                         tests/palette_dmenu_check.py \
                         tests/palette_commands_check.py \
                         tests/palette_extensions_check.py \
                         tests/palette_route_check.py \
                         tests/palette_shortcut_check.py \
                         tests/palette_dictation_check.py \
                         tests/catalog_check.py \
                         tests/applications_check.py \
                         tests/voice_session_check.py \
                         tests/codex_session_check.py \
                         tests/matching_session_check.py \
                         tests/clipboard_transfer_check.py \
                         tests/files_check.py \
                         extensions/browser-search/tests/palette_check.py \
                         extensions/gif-search/tests/palette_check.py \
                         extensions/translate/tests/palette_check.py; do
                  echo "== $f =="
                  python3 "$f"
                done
                touch $out
              '';

          migrate-state =
            pkgs.runCommand "nixarchy-menu-check-migrate-state"
              {
                nativeBuildInputs = [
                  pkgs.python3
                  pkgs.jq
                ];
              }
              ''
                export HOME=$TMPDIR
                python3 ${checkSrc}/tests/migrate_state_check.py
                touch $out
              '';

          # A silent SKIP (tokenizers not importable) must not pass CI: it
          # would mean the parity test never actually ran.
          engine =
            pkgs.runCommand "nixarchy-menu-check-engine" { nativeBuildInputs = [ engineCheckPython ]; }
              ''
                export HOME=$TMPDIR
                set -o pipefail
                python3 ${checkSrc}/tests/matching_engine_check.py \
                  --engine ${matching-engine}/bin/keystroke-matching \
                  --model-dir ${model-small} | tee $TMPDIR/engine-output
                if grep -q '^SKIP' $TMPDIR/engine-output; then
                  echo "tokenizer parity was skipped; tokenizers is not importable" >&2
                  exit 1
                fi
                touch $out
              '';

          shellcheck =
            pkgs.runCommand "nixarchy-menu-check-shellcheck" { nativeBuildInputs = [ pkgs.shellcheck ]; }
              ''
                shellcheck ${checkSrc}/helpers/*.sh ${checkSrc}/bin/nixarchy-menu
                touch $out
              '';
        }
      );

      devShells = forAll (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              qt6.qtdeclarative
              qt6.qtbase
              quickshell
              (python3.withPackages (p: [ p.tokenizers ]))
              jq
              fd
              ripgrep
              shellcheck
            ];
          };
        }
      );
    };
}
