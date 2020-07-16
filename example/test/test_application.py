import pytest

import example.application


@pytest.mark.asyncio
async def test_application_life_cycle():

    # Closing should not fail if not existent.
    await example.application.close_application()

    # Getting should fail if not existent.
    with pytest.raises(AssertionError):
        await example.application.get_application()

    # After init getting should work.
    app = await example.application.init_application()
    assert isinstance(app, example.application.Application)

    # Now it should be possible to get it.
    assert await example.application.get_application() is app

    # Init while existent should fail.
    with pytest.raises(AssertionError):
        await example.application.init_application()
    # but getting should still work.
    assert await example.application.get_application() is app

    # Closing should make it not existent.
    await example.application.close_application()
    with pytest.raises(AssertionError):
        await example.application.get_application()

    # Make sure closing more than once is okay.
    await example.application.close_application()

    # Make sure we can init it again.
    new = await example.application.init_application()
    assert new is not app
    assert isinstance(new, example.application.Application)
