import QtQuick
import QtTest
import "../providers" as Providers

TestCase {
  id: testCase
  name: "ApplicationsConnection"
  when: windowShown
  property int settled: 0

  function settleConnections() {
    var next = settled + 1
    Qt.callLater(function() { testCase.settled = next })
    tryCompare(testCase, "settled", next)
  }

  QtObject { id: firstLibrary; signal appsChanged() }
  QtObject { id: secondLibrary; signal appsChanged() }
  Item {
    id: testHost
    property var appLibrary: firstLibrary
    property int requeries: 0
    function requery(request) { requeries++ }
  }
  Component { id: providerComponent; Providers.Applications { } }
  Loader { id: asyncLoader; asynchronous: true }

  function init() {
    testHost.appLibrary = firstLibrary
    testHost.requeries = 0
  }

  function cleanup() {
    asyncLoader.active = false
    asyncLoader.sourceComponent = undefined
    wait(0)
  }

  function test_deferred_connection_and_rebinding() {
    var provider = providerComponent.createObject(testCase, { host: testHost })
    verify(provider !== null)
    var initial = testHost.requeries
    firstLibrary.appsChanged()
    compare(testHost.requeries, initial)
    settleConnections()
    provider.searchCache = { stale: true }
    firstLibrary.appsChanged()
    compare(testHost.requeries, initial + 1)
    compare(Object.keys(provider.searchCache).length, 0)

    testHost.appLibrary = secondLibrary
    var rebound = testHost.requeries
    firstLibrary.appsChanged()
    compare(testHost.requeries, rebound)
    secondLibrary.appsChanged()
    compare(testHost.requeries, rebound + 1)

    provider.host = null
    var detached = testHost.requeries
    secondLibrary.appsChanged()
    compare(testHost.requeries, detached)
    provider.destroy()
    wait(0)
    var destroyed = testHost.requeries
    secondLibrary.appsChanged()
    compare(testHost.requeries, destroyed)
  }

  function test_async_creation_and_immediate_destruction() {
    for (var i = 0; i < 30; i++) {
      asyncLoader.active = true
      asyncLoader.sourceComponent = providerComponent
      tryCompare(asyncLoader, "status", Loader.Ready)
      asyncLoader.item.host = testHost
      settleConnections()
      var initial = testHost.requeries
      firstLibrary.appsChanged()
      compare(testHost.requeries, initial + 1)
      asyncLoader.active = false
      wait(0)
    }
    for (var j = 0; j < 30; j++) {
      var provider = providerComponent.createObject(testCase, { host: testHost })
      provider.destroy()
      wait(0)
    }
  }
}
