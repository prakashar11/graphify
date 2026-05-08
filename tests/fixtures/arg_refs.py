from graphql import GraphQLSchema


def build_context(request):
    return {"user_id": request.headers.get("x-user-id")}


# dict literal as return value — Gap 2 pattern
def build_config():
    return {"context": build_context, "debug": True}


# dict literal passed as positional call argument — Gap 1 pattern
def build_server_dict_arg():
    return GraphQLSchema({"context": build_context})


def build_server():
    return GraphQLSchema(context=build_context)


def pass_around(fn):
    return fn


def call_with_ref():
    pass_around(build_context)


def multi_arg(a, fn, b):
    pass
