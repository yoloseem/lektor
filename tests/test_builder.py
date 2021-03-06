def get_child_sources(prog):
    return sorted(list(prog.iter_child_sources()), key=lambda x: x['_id'])


def test_basic_build(pad, builder):
    root = pad.root

    prog, build_state = builder.build(root)
    assert prog.source is root
    assert build_state.failed_artifacts == []
    assert build_state.updated_artifacts == prog.artifacts

    artifact, = prog.artifacts
    assert artifact.artifact_name == 'index.html'
    assert artifact.sources == [root.source_filename]
    assert artifact.updated
    assert artifact.extra is None
    assert artifact.config_hash is None


def test_child_sources_basic(pad, builder):
    extra = pad.get('/extra')

    prog, _ = builder.build(extra)
    child_sources = get_child_sources(prog)

    assert [x['_id'] for x in child_sources] == [
        'a',
        'b',
        'hello.txt',
    ]


def test_child_sources_pagination(pad, builder):
    projects = pad.get('/projects')

    prog, _ = builder.build(projects)

    child_sources = get_child_sources(prog)

    assert len(child_sources) == 2
    assert child_sources[0]['_id'] == 'projects'
    assert child_sources[0].page_num == 1
    assert child_sources[1]['_id'] == 'projects'
    assert child_sources[1].page_num == 2

    prog, _ = builder.build(child_sources[0])
    child_sources_p1 = get_child_sources(prog)

    assert [x['_id'] for x in child_sources_p1] == [
        'attachment.txt',
        'bagpipe',
        'coffee',
        'master',
        'oven',
        'secret',
    ]

    prog, _ = builder.build(child_sources[1])
    child_sources_p2 = get_child_sources(prog)

    assert [x['_id'] for x in child_sources_p2] == [
        'postage',
        'slave',
        'wolf',
    ]


def test_basic_artifact_current_test(pad, builder, reporter):
    root = pad.root

    def build():
        reporter.clear()
        prog, _ = builder.build(root)
        return prog.artifacts[0]

    artifact = build()

    assert reporter.get_major_events() == [
        ('enter-source', {
            'source': root,
        }),
        ('start-artifact-build', {
            'artifact': artifact,
            'is_current': False,
        }),
        ('build-func', {
            'func': 'lektor.build_programs.PageBuildProgram',
        }),
        ('finish-artifact-build', {
            'artifact': artifact,
        }),
        ('leave-source', {
            'source': root,
        })
    ]

    assert reporter.get_recorded_dependencies() == [
        'Website.lektorproject',
        'content/contents.lr',
        'flowblocks/text.ini',
        'templates/blocks/text.html',
        'templates/layout.html',
        'templates/page.html'
    ]

    assert artifact.is_current

    artifact = build()

    assert artifact.is_current

    assert reporter.get_major_events() == [
        ('enter-source', {
            'source': root
        }),
        ('start-artifact-build', {
            'artifact': artifact,
            'is_current': True,
        }),
        ('build-func', {
            'func': 'lektor.build_programs.PageBuildProgram',
        }),
        ('finish-artifact-build', {
            'artifact': artifact,
        }),
        ('leave-source', {
            'source': root,
        })
    ]


def test_basic_template_rendering(pad, builder):
    root = pad.root

    prog, _ = builder.build(root)
    artifact = prog.artifacts[0]

    with artifact.open('rb') as f:
        rv = f.read().decode('utf-8')

    assert artifact.artifact_name == 'index.html'

    assert '<title>My Website</title>' in rv
    assert '<h1>Welcome</h1>' in rv
    assert '<link href="./static/style.css" rel="stylesheet">' in rv
    assert '<p>Welcome to this pretty nifty website.</p>' in rv


def test_attachment_copying(pad, builder):
    root = pad.root
    text_file = root.attachments.get('hello.txt')

    prog, _ = builder.build(text_file)
    artifact = prog.artifacts[0]

    assert artifact.artifact_name == 'hello.txt'

    with artifact.open('rb') as f:
        rv = f.read().decode('utf-8').strip()
        assert rv == 'Hello I am an Attachment'


def test_asset_processing(pad, builder):
    static = pad.asset_root.get_child('static')

    prog, _ = builder.build(static)
    assets = list(prog.iter_child_sources())
    assert len(assets) == 1
    assert assets[0].name == 'demo.css'

    prog, _ = builder.build(assets[0])
    with prog.artifacts[0].open('rb') as f:
        rv = f.read().decode('utf-8').strip()
        assert 'color: red' in rv
