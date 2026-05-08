import { ApolloServer } from 'apollo-server';

function buildContext(req: unknown): { userId: string } {
  return { userId: 'user-1' };
}

function buildConfig() {
  return { context: buildContext, debug: true };
}

// Apollo pattern: buildConfig returns the object, new ApolloServer receives it indirectly
const buildConfigArrow = (gateway: unknown) => ({ context: buildContext, gateway });

function buildServer() {
  const config = buildConfig();
  return new ApolloServer({ context: buildContext, schema: null });
}

// Indirect pattern: new ApolloServer(buildConfigArrow(gw)) — context is inside arrow fn return
function buildServerIndirect(gw: unknown) {
  return new ApolloServer(buildConfigArrow(gw));
}

function passAround(fn: Function) {
  return fn;
}

function callWithRef() {
  passAround(buildContext);
}
