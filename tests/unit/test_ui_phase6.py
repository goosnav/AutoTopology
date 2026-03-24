"""Phase 6 — UI & Review Loop tests.

Covers:
  - RunSession state machine
  - GalleryService filtering / sorting / paging
  - ReviewService top-K selection + pairwise tie-breaks
  - PreferenceStore CRUD
  - New API endpoints (run control, gallery, candidate detail, review, export)
"""

from __future__ import annotations

import json
import random
import tempfile
import uuid
from copy import deepcopy
from pathlib import Path
from typing import List

import pytest
from fastapi.testclient import TestClient

from core.evolution.candidate import Candidate
from core.genome.gene_types import GeneSpec, GeneType
from core.genome.genome import Genome

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SIMPLE_CATALOG: list[GeneSpec] = [
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["table_family"], default="table_family"),
    GeneSpec("subtype", GeneType.CATEGORICAL, layer=1,
             categories=["dining", "coffee", "side"], default="dining"),
    GeneSpec("width", GeneType.CONTINUOUS, layer=3,
             min_val=100.0, max_val=500.0, default=200.0),
    GeneSpec("support_count", GeneType.INTEGER, layer=2,
             min_val=1, max_val=8, default=4),
    GeneSpec("symmetric", GeneType.BOOLEAN, layer=1, default=True),
]


def _genome(seed: int = 42, **overrides) -> Genome:
    rng = random.Random(seed)
    g = Genome.random_init(SIMPLE_CATALOG, rng)
    g.genes.update(overrides)
    return g


def _candidate(
    physics=0.5, aesthetic=0.5, novelty=0.5,
    valid=True, family="table_family",
    subtype="dining", seed=None, island_id="i0", league_id="l0",
) -> Candidate:
    rng = random.Random(seed or random.randint(0, 9999))
    g = Genome.random_init(SIMPLE_CATALOG, rng)
    g.genes["subtype"] = subtype
    c = Candidate(
        genome=g,
        family=family,
        physics_score=physics,
        aesthetic_score=aesthetic,
        novelty_score=novelty,
        is_valid=valid,
    )
    c.metadata["island_id"] = island_id
    c.metadata["league_id"] = league_id
    c.metadata["generation"] = 1
    return c


def _make_population(n: int = 10) -> List[Candidate]:
    pop = []
    for i in range(n):
        c = _candidate(
            physics=i / (n - 1) if n > 1 else 0.5,
            aesthetic=(n - 1 - i) / (n - 1) if n > 1 else 0.5,
            seed=i,
        )
        c.metadata["generation"] = i % 3 + 1
        pop.append(c)
    return pop


# ===========================================================================
# 1. RunSession
# ===========================================================================

class TestRunSession:
    def _session(self, pop_size=6):
        from app.services.run_session import RunSession, RunState
        from core.leagues.island import Island
        from core.leagues.league import League
        from core.evolution.engine import EvolutionEngine

        islands = []
        for i in range(2):
            pop = [_candidate(seed=i * 10 + j) for j in range(pop_size)]
            islands.append(Island(
                island_id=f"i{i}", league_id="l0",
                population=pop, catalog=SIMPLE_CATALOG,
                rng=random.Random(i), mutation_rate=0.3, crossover_rate=0.7,
            ))
        league = League(league_id="l0", islands=islands, migration_rate=0.2, migration_interval=2)
        engine = EvolutionEngine(
            leagues=[league], catalog=SIMPLE_CATALOG,
            physics_weight=1/3, aesthetic_weight=1/3, novelty_weight=1/3,
            n_offspring_per_island=3,
        )
        return RunSession(engine=engine, review_every_n_generations=2)

    def test_initial_state_is_idle(self):
        from app.services.run_session import RunState
        s = self._session()
        assert s.state == RunState.IDLE

    def test_start_changes_state_to_running(self):
        from app.services.run_session import RunState
        s = self._session()
        s.start()
        assert s.state == RunState.RUNNING

    def test_cannot_start_twice(self):
        from app.services.run_session import RunState, RunSessionError
        s = self._session()
        s.start()
        with pytest.raises(RunSessionError):
            s.start()

    def test_pause_changes_state(self):
        from app.services.run_session import RunState
        s = self._session()
        s.start()
        s.pause()
        assert s.state == RunState.PAUSED

    def test_resume_from_paused(self):
        from app.services.run_session import RunState
        s = self._session()
        s.start()
        s.pause()
        s.resume()
        assert s.state == RunState.RUNNING

    def test_stop_terminates_session(self):
        from app.services.run_session import RunState
        s = self._session()
        s.start()
        s.stop()
        assert s.state == RunState.STOPPED

    def test_step_increments_generation(self):
        s = self._session()
        s.start()
        s.step()
        assert s.engine.generation == 1

    def test_step_not_allowed_when_stopped(self):
        from app.services.run_session import RunSessionError
        s = self._session()
        s.start()
        s.stop()
        with pytest.raises(RunSessionError):
            s.step()

    def test_review_boundary_detected(self):
        s = self._session()
        s.start()
        for _ in range(s.review_every_n_generations):
            s.step()
        assert s.at_review_boundary()

    def test_status_dict(self):
        s = self._session()
        status = s.status()
        assert "state" in status
        assert "generation" in status
        assert "candidate_count" in status


# ===========================================================================
# 2. GalleryService
# ===========================================================================

class TestGalleryService:
    def _gallery(self, n=12):
        from app.services.gallery_service import GalleryService
        pop = _make_population(n)
        return GalleryService(candidates=pop)

    def test_list_returns_all_by_default(self):
        g = self._gallery(10)
        result = g.list()
        assert len(result) == 10

    def test_sort_by_physics_desc(self):
        g = self._gallery(10)
        result = g.list(sort_by="physics", descending=True)
        scores = [c.physics_score for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_novelty_desc(self):
        g = self._gallery(10)
        result = g.list(sort_by="novelty", descending=True)
        scores = [c.novelty_score for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_aesthetic_asc(self):
        g = self._gallery(10)
        result = g.list(sort_by="aesthetic", descending=False)
        scores = [c.aesthetic_score for c in result]
        assert scores == sorted(scores)

    def test_filter_by_valid_only(self):
        from app.services.gallery_service import GalleryService
        pop = [_candidate(valid=True) for _ in range(5)]
        pop += [_candidate(valid=False) for _ in range(5)]
        g = GalleryService(candidates=pop)
        result = g.list(valid_only=True)
        assert all(c.is_valid for c in result)
        assert len(result) == 5

    def test_filter_by_family(self):
        from app.services.gallery_service import GalleryService
        pop = [_candidate(family="table_family") for _ in range(5)]
        pop += [_candidate(family="lamp_family") for _ in range(3)]
        g = GalleryService(candidates=pop)
        result = g.list(family_filter="table_family")
        assert all(c.family == "table_family" for c in result)
        assert len(result) == 5

    def test_pagination_page_0(self):
        g = self._gallery(10)
        page = g.list(page=0, page_size=4)
        assert len(page) == 4

    def test_pagination_last_page(self):
        g = self._gallery(10)
        page = g.list(page=2, page_size=4)
        assert len(page) == 2  # 10 items, page 2 of size 4 = items 8-9

    def test_get_by_id(self):
        g = self._gallery(5)
        all_candidates = g.list()
        target = all_candidates[2]
        found = g.get_by_id(target.candidate_id)
        assert found is not None
        assert found.candidate_id == target.candidate_id

    def test_get_by_id_missing_returns_none(self):
        g = self._gallery(5)
        assert g.get_by_id("nonexistent_id") is None

    def test_sort_by_generation(self):
        g = self._gallery(10)
        result = g.list(sort_by="generation", descending=True)
        gens = [c.metadata.get("generation", 0) for c in result]
        assert gens == sorted(gens, reverse=True)

    def test_total_count(self):
        g = self._gallery(10)
        assert g.total_count() == 10


# ===========================================================================
# 3. ReviewService
# ===========================================================================

class TestReviewService:
    def _review(self, n=8):
        from app.services.review_service import ReviewService
        pop = _make_population(n)
        return ReviewService(candidates=pop)

    def test_submit_top_k_marks_selected(self):
        r = self._review(8)
        all_ids = [c.candidate_id for c in r.candidates]
        selected_ids = all_ids[:3]
        r.submit_top_k(selected_ids)
        for c in r.candidates:
            if c.candidate_id in selected_ids:
                assert c.human_selected

    def test_top_k_boosts_score(self):
        r = self._review(8)
        target = r.candidates[0]
        score_before = target.combined_score(1/3, 1/3, 1/3)
        r.submit_top_k([target.candidate_id])
        score_after = target.combined_score(1/3, 1/3, 1/3)
        assert score_after > score_before

    def test_submit_pairwise_records_preference(self):
        r = self._review(8)
        winner = r.candidates[0]
        loser = r.candidates[1]
        r.submit_pairwise(winner_id=winner.candidate_id, loser_id=loser.candidate_id)
        prefs = r.get_pairwise_history()
        assert len(prefs) == 1
        assert prefs[0]["winner"] == winner.candidate_id
        assert prefs[0]["loser"] == loser.candidate_id

    def test_pairwise_invalid_id_raises(self):
        from app.services.review_service import ReviewError
        r = self._review(8)
        with pytest.raises(ReviewError):
            r.submit_pairwise(winner_id="bad_id", loser_id=r.candidates[0].candidate_id)

    def test_submit_top_k_invalid_id_raises(self):
        from app.services.review_service import ReviewError
        r = self._review(8)
        with pytest.raises(ReviewError):
            r.submit_top_k(["completely_fake_id"])

    def test_get_shortlist_returns_human_selected(self):
        r = self._review(8)
        ids = [c.candidate_id for c in r.candidates[:3]]
        r.submit_top_k(ids)
        shortlist = r.get_shortlist()
        assert len(shortlist) == 3
        assert all(c.human_selected for c in shortlist)

    def test_clear_review_resets_selection(self):
        r = self._review(8)
        ids = [c.candidate_id for c in r.candidates[:3]]
        r.submit_top_k(ids)
        r.clear()
        assert r.get_shortlist() == []

    def test_pairwise_history_accumulates(self):
        r = self._review(8)
        for i in range(3):
            r.submit_pairwise(
                winner_id=r.candidates[i].candidate_id,
                loser_id=r.candidates[i + 4].candidate_id,
            )
        assert len(r.get_pairwise_history()) == 3


# ===========================================================================
# 4. PreferenceStore
# ===========================================================================

class TestPreferenceStore:
    def _store(self, tmp_path: Path):
        from preference.persistence.preference_store import PreferenceStore
        return PreferenceStore(path=tmp_path / "prefs.jsonl")

    def test_append_and_load(self, tmp_path):
        store = self._store(tmp_path)
        store.append({"winner": "aaa", "loser": "bbb", "ts": 1})
        store.append({"winner": "ccc", "loser": "ddd", "ts": 2})
        records = store.load_all()
        assert len(records) == 2
        assert records[0]["winner"] == "aaa"

    def test_load_empty_file(self, tmp_path):
        store = self._store(tmp_path)
        assert store.load_all() == []

    def test_load_missing_file_returns_empty(self, tmp_path):
        from preference.persistence.preference_store import PreferenceStore
        store = PreferenceStore(path=tmp_path / "nonexistent.jsonl")
        assert store.load_all() == []

    def test_count(self, tmp_path):
        store = self._store(tmp_path)
        for i in range(5):
            store.append({"winner": f"w{i}", "loser": f"l{i}", "ts": i})
        assert store.count() == 5

    def test_clear(self, tmp_path):
        store = self._store(tmp_path)
        store.append({"winner": "a", "loser": "b", "ts": 1})
        store.clear()
        assert store.count() == 0

    def test_persistence_across_instances(self, tmp_path):
        from preference.persistence.preference_store import PreferenceStore
        p = tmp_path / "prefs.jsonl"
        s1 = PreferenceStore(path=p)
        s1.append({"winner": "x", "loser": "y", "ts": 0})
        s2 = PreferenceStore(path=p)
        assert s2.count() == 1


# ===========================================================================
# 5. ExportService
# ===========================================================================

class TestExportService:
    def test_export_creates_files(self, tmp_path):
        from app.services.export_service import ExportService
        c = _candidate()
        svc = ExportService(export_dir=tmp_path)
        result = svc.export(c)
        assert result["metadata_path"] is not None
        meta_path = Path(result["metadata_path"])
        assert meta_path.exists()

    def test_export_metadata_contains_key_fields(self, tmp_path):
        from app.services.export_service import ExportService
        c = _candidate(physics=0.7, aesthetic=0.6, novelty=0.5)
        svc = ExportService(export_dir=tmp_path)
        result = svc.export(c)
        meta = json.loads(Path(result["metadata_path"]).read_text())
        assert "candidate_id" in meta
        assert "family" in meta
        assert "physics_score" in meta
        assert "genes" in meta

    def test_export_duplicate_candidate_allowed(self, tmp_path):
        from app.services.export_service import ExportService
        c = _candidate()
        svc = ExportService(export_dir=tmp_path)
        r1 = svc.export(c)
        r2 = svc.export(c)
        # Both calls succeed
        assert r1["candidate_id"] == r2["candidate_id"]

    def test_export_returns_candidate_id(self, tmp_path):
        from app.services.export_service import ExportService
        c = _candidate()
        svc = ExportService(export_dir=tmp_path)
        result = svc.export(c)
        assert result["candidate_id"] == c.candidate_id


# ===========================================================================
# 6. API Endpoints
# ===========================================================================

@pytest.fixture()
def client():
    """FastAPI test client with a fresh app instance."""
    from app.api.main import app
    return TestClient(app)


@pytest.fixture()
def seeded_client():
    """Test client with a pre-seeded run session."""
    from app.api.main import app
    from app.services.run_session import RunSession, RunState
    from core.leagues.island import Island
    from core.leagues.league import League
    from core.evolution.engine import EvolutionEngine

    # Build a minimal engine
    pop = [_candidate(seed=i) for i in range(8)]
    island = Island(
        island_id="i0", league_id="l0",
        population=pop, catalog=SIMPLE_CATALOG,
        rng=random.Random(0), mutation_rate=0.3, crossover_rate=0.7,
    )
    league = League(league_id="l0", islands=[island],
                    migration_rate=0.1, migration_interval=3)
    engine = EvolutionEngine(
        leagues=[league], catalog=SIMPLE_CATALOG,
        n_offspring_per_island=3,
    )
    session = RunSession(engine=engine, review_every_n_generations=2)
    # Inject into the app's state (also init dependent services)
    from app.api import state as app_state
    from app.services.gallery_service import GalleryService
    from app.services.review_service import ReviewService
    from app.services.export_service import ExportService
    import tempfile

    app_state.run_session = session
    all_c = session.engine.get_all_candidates()
    app_state.gallery_service = GalleryService(candidates=all_c)
    app_state.review_service = ReviewService(candidates=all_c)
    app_state.export_service = ExportService(
        export_dir=Path(tempfile.mkdtemp())
    )

    yield TestClient(app)

    # Cleanup
    app_state.run_session = None
    app_state.gallery_service = None
    app_state.review_service = None
    app_state.export_service = None


class TestRunEndpoints:
    def test_run_status_returns_200(self, client):
        resp = client.get("/api/run/status")
        assert resp.status_code == 200

    def test_run_status_has_state_field(self, client):
        resp = client.get("/api/run/status")
        data = resp.json()
        assert "state" in data

    def test_run_start_creates_session(self, client):
        resp = client.post("/api/run/start", json={
            "family": "table_family",
            "population_count": 6,
            "islands_per_league": 1,
            "league_count": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] in ("running", "idle", "paused")

    def test_run_stop_endpoint(self, seeded_client):
        seeded_client.post("/api/run/start", json={
            "family": "table_family",
            "population_count": 6,
            "islands_per_league": 1,
            "league_count": 1,
        })
        resp = seeded_client.post("/api/run/stop")
        assert resp.status_code == 200

    def test_run_step_endpoint(self, seeded_client):
        from app.api import state as app_state
        app_state.run_session.start()
        resp = seeded_client.post("/api/run/step")
        assert resp.status_code == 200
        data = resp.json()
        assert data["generation"] >= 1


class TestGalleryEndpoints:
    def test_gallery_endpoint_returns_200(self, seeded_client):
        resp = seeded_client.get("/api/gallery")
        assert resp.status_code == 200

    def test_gallery_returns_list(self, seeded_client):
        resp = seeded_client.get("/api/gallery")
        data = resp.json()
        assert "candidates" in data
        assert isinstance(data["candidates"], list)

    def test_gallery_sort_param(self, seeded_client):
        resp = seeded_client.get("/api/gallery?sort_by=physics&descending=true")
        assert resp.status_code == 200

    def test_gallery_pagination_params(self, seeded_client):
        resp = seeded_client.get("/api/gallery?page=0&page_size=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["candidates"]) <= 3

    def test_candidate_detail_endpoint(self, seeded_client):
        gallery = seeded_client.get("/api/gallery").json()
        if gallery["candidates"]:
            cid = gallery["candidates"][0]["candidate_id"]
            resp = seeded_client.get(f"/api/candidate/{cid}")
            assert resp.status_code == 200
            detail = resp.json()
            assert detail["candidate_id"] == cid

    def test_candidate_detail_404_for_unknown(self, seeded_client):
        resp = seeded_client.get("/api/candidate/nonexistent_xyz")
        assert resp.status_code == 404


class TestReviewEndpoints:
    def test_review_submit_top_k(self, seeded_client):
        gallery = seeded_client.get("/api/gallery").json()
        ids = [c["candidate_id"] for c in gallery["candidates"][:2]]
        resp = seeded_client.post("/api/review/select", json={"candidate_ids": ids})
        assert resp.status_code == 200

    def test_review_pairwise_submit(self, seeded_client):
        gallery = seeded_client.get("/api/gallery").json()
        candidates = gallery["candidates"]
        if len(candidates) >= 2:
            resp = seeded_client.post("/api/review/pairwise", json={
                "winner_id": candidates[0]["candidate_id"],
                "loser_id": candidates[1]["candidate_id"],
            })
            assert resp.status_code == 200


class TestExportEndpoints:
    def test_export_candidate_endpoint(self, seeded_client):
        gallery = seeded_client.get("/api/gallery").json()
        if gallery["candidates"]:
            cid = gallery["candidates"][0]["candidate_id"]
            resp = seeded_client.post(f"/api/export/{cid}")
            assert resp.status_code == 200
            data = resp.json()
            assert "candidate_id" in data
            assert "metadata_path" in data

    def test_export_unknown_returns_404(self, seeded_client):
        resp = seeded_client.post("/api/export/no_such_candidate")
        assert resp.status_code == 404
