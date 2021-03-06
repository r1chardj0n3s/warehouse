# Copyright 2013 Donald Stufft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import textwrap

import pretend
import pytest

from werkzeug.exceptions import NotFound

from warehouse.packaging.views import project_detail


def test_project_detail_missing_project():
    app = pretend.stub(
        db=pretend.stub(
            packaging=pretend.stub(
                get_project=pretend.call_recorder(lambda proj: None),
            ),
        ),
    )
    request = pretend.stub()

    project_name = "test-project"

    with pytest.raises(NotFound):
        project_detail(app, request, project_name)

    assert app.db.packaging.get_project.calls == [
        pretend.call("test-project"),
    ]


def test_project_detail_no_versions():
    app = pretend.stub(
        db=pretend.stub(
            packaging=pretend.stub(
                get_project=pretend.call_recorder(
                    lambda proj: "test-project",
                ),
                get_releases=pretend.call_recorder(lambda proj: []),
            ),
        ),
    )
    request = pretend.stub()

    project_name = "test-project"

    with pytest.raises(NotFound):
        project_detail(app, request, project_name)

    assert app.db.packaging.get_project.calls == [
        pretend.call("test-project"),
    ]
    assert app.db.packaging.get_releases.calls == [
        pretend.call("test-project"),
    ]


def test_project_detail_redirects():
    app = pretend.stub(
        config=pretend.stub(
            cache=pretend.stub(
                browser=False,
                varnish=False,
            ),
        ),
        db=pretend.stub(
            packaging=pretend.stub(
                get_project=pretend.call_recorder(
                    lambda proj: "test-project",
                ),
                get_releases=pretend.call_recorder(
                    lambda proj: [{"version": "1.0"}],
                ),
            ),
        ),
    )
    request = pretend.stub(
        url_adapter=pretend.stub(
            build=pretend.call_recorder(
                lambda *a, **kw: "/projects/test-project/",
            ),
        ),
    )

    project_name = "test-Project"
    normalized = "test-project"

    resp = project_detail(app, request, project_name=project_name)

    assert resp.status_code == 301
    assert resp.headers["Location"] == "/projects/test-project/"

    assert resp.headers["Surrogate-Key"] == \
        "project project/{}".format(normalized)

    assert app.db.packaging.get_project.calls == [
        pretend.call("test-Project"),
    ]
    assert app.db.packaging.get_releases.calls == [
        pretend.call("test-project"),
    ]
    assert request.url_adapter.build.calls == [
        pretend.call(
            "warehouse.packaging.views.project_detail",
            {"project_name": "test-project", "version": None},
            force_external=False,
        ),
    ]


def test_project_detail_invalid_version():
    app = pretend.stub(
        config=pretend.stub(
            cache=pretend.stub(
                browser=False,
                varnish=False,
            ),
        ),
        db=pretend.stub(
            packaging=pretend.stub(
                get_project=pretend.call_recorder(
                    lambda proj: "test-project",
                ),
                get_releases=pretend.call_recorder(
                    lambda proj: [{"version": "1.0"}],
                ),
            ),
        ),
    )
    request = pretend.stub()

    project_name = "test-project"

    with pytest.raises(NotFound):
        project_detail(app, request, project_name, "2.0")

    assert app.db.packaging.get_project.calls == [
        pretend.call("test-project"),
    ]
    assert app.db.packaging.get_releases.calls == [
        pretend.call("test-project"),
    ]


@pytest.mark.parametrize(("version", "description", "camo"), [
    (
        None,
        textwrap.dedent("""
            Test Project
            ============

            This is a test project
        """),
        None,
    ),
    (
        "1.0",
        textwrap.dedent("""
            Test Project
            ============

            This is a test project
        """),
        None,
    ),
    (None, ".. code-fail::\n    wat", None),
    ("1.0", ".. code-fail::\n    wat", None),
    (None, None, None),
    ("1.0", None, None),
    (
        None,
        textwrap.dedent("""
            Test Project
            ============

            This is a test project
        """),
        pretend.stub(url="https://camo.example.com/", key="secret key"),
    ),
    (
        "1.0",
        textwrap.dedent("""
            Test Project
            ============

            This is a test project
        """),
        pretend.stub(url="https://camo.example.com/", key="secret key"),
    ),
    (
        None,
        ".. code-fail::\n    wat",
        pretend.stub(url="https://camo.example.com/", key="secret key"),
    ),
    (
        "1.0",
        ".. code-fail::\n    wat",
        pretend.stub(url="https://camo.example.com/", key="secret key"),
    ),
    (
        None,
        None,
        pretend.stub(url="https://camo.example.com/", key="secret key"),
    ),
    (
        "1.0",
        None,
        pretend.stub(url="https://camo.example.com/", key="secret key"),
    ),
])
def test_project_detail_valid(version, description, camo):
    release = {
        "description": description,
        "requires_dist": ["foo", "xyz > 0.1"]
    }

    template = pretend.stub(
        render=pretend.call_recorder(lambda **ctx: ""),
    )

    app = pretend.stub(
        config=pretend.stub(
            cache=pretend.stub(
                browser=False,
                varnish=False,
            ),
            camo=camo,
        ),
        db=pretend.stub(
            packaging=pretend.stub(
                get_project=pretend.call_recorder(
                    lambda proj: "test-project",
                ),
                get_releases=pretend.call_recorder(
                    lambda proj: [{"version": "2.0"}, {"version": "1.0"}],
                ),
                get_release=pretend.call_recorder(
                    lambda proj, version: release,
                ),
                get_download_counts=pretend.call_recorder(
                    lambda proj: {
                        "last_day": 1,
                        "last_week": 7,
                        "last_month": 30,
                    },
                ),
                get_downloads=pretend.call_recorder(lambda proj, ver: []),
                get_classifiers=pretend.call_recorder(lambda proj, ver: []),
                get_documentation_url=pretend.call_recorder(
                    lambda proj: None,
                ),
                get_bugtrack_url=pretend.call_recorder(lambda proj: None),
                get_users_for_project=pretend.call_recorder(lambda proj: []),
            ),
        ),
        templates=pretend.stub(
            get_template=pretend.call_recorder(lambda t: template),
        ),
    )
    request = pretend.stub(
        url_adapter=pretend.stub(build=lambda *a,
                                 **kw: "/projects/test-project/")
    )

    project_name = "test-project"
    normalized = "test-project"

    resp = project_detail(
        app,
        request,
        project_name=project_name,
        version=version,
    )

    assert resp.status_code == 200

    assert resp.headers["Surrogate-Key"] == \
        "project project/{}".format(normalized)

    assert app.db.packaging.get_project.calls == [
        pretend.call("test-project"),
    ]
    assert app.db.packaging.get_releases.calls == [
        pretend.call("test-project"),
    ]
    assert app.db.packaging.get_users_for_project.calls == [
        pretend.call("test-project"),
    ]
