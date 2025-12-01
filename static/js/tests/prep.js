// Runs before Jest's test framework is installed.
// Provide a Node-style "global" for libs that expect it.
if (!globalThis.global) globalThis.global = globalThis;