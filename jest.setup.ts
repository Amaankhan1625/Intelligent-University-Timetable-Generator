import '@testing-library/jest-dom'
import 'whatwg-fetch'
import { TextEncoder, TextDecoder } from 'util'

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder
}

if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder
}
// Mock BroadcastChannel for Jest tests since it's not available
class BroadcastChannel {
  constructor(name: string) {
    this.name = name;
    this.onmessage = () => {};
  }
  postMessage(msg: any) {}
  close() {}
}

global.BroadcastChannel = global.BroadcastChannel || BroadcastChannel;
