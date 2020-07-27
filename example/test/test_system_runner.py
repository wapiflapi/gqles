import pytest

import example.application


@pytest.mark.asyncio
async def test_system_runner_life_cycle():

    # Closing should not fail if not existent.
    await example.application.close_system_runner()

    # Getting should fail if not existent.
    with pytest.raises(AssertionError):
        await example.application.get_system_runner()

    # After init getting should work.
    app = await example.application.init_system_runner()
    assert isinstance(app, example.application.SystemRunner)

    # Now it should be possible to get it.
    assert await example.application.get_system_runner() is app

    # Init while existent should fail.
    with pytest.raises(AssertionError):
        await example.application.init_system_runner()
    # but getting should still work.
    assert await example.application.get_system_runner() is app

    # Closing should make it not existent.
    await example.application.close_system_runner()
    with pytest.raises(AssertionError):
        await example.application.get_system_runner()

    # Make sure closing more than once is okay.
    await example.application.close_system_runner()

    # Make sure we can init it again.
    new = await example.application.init_system_runner()
    assert new is not app
    assert isinstance(new, example.application.SystemRunner)
