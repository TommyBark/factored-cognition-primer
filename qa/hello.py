from ice.recipe import recipe


def another_func():
    return "This is another function"


async def another_func_async():
    return "This is another async function"


async def say_hello():
    result = another_func()  # only async functions are traced
    result2 = await another_func_async()  # this is traced
    return "Hello, World!"


# recipe.main is used to denote the recipe entry point, entry point must be async.
# They should be async because model calls should be as parallelized as possible.
recipe.main(say_hello)
