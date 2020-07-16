import example.domain


def test_world():

    exandria = example.domain.World.__create__(ruler="Matt Mercer")
    assert exandria.ruler == "Matt Mercer"

    exandria.storytell('Chroma Conclave')
    exandria.storytell('Vecna')

    assert exandria.history == ('Chroma Conclave', 'Vecna'), \
        exandria.history

    exandria.ruler = 'Vox Machina'
    assert exandria.ruler == 'Vox Machina'
