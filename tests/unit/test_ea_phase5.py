"""Phase 5 EA Core tests — candidate, novelty, selection, mutation,
crossover, repair, MAP-Elites archive, island/league, engine."""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

import pytest

from core.genome.gene_types import GeneSpec, GeneType
from core.genome.genome import Genome

# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

SIMPLE_CATALOG: list[GeneSpec] = [
    GeneSpec("width", GeneType.CONTINUOUS, layer=3, min_val=100.0, max_val=500.0, default=200.0),
    GeneSpec("height", GeneType.CONTINUOUS, layer=3, min_val=100.0, max_val=500.0, default=300.0),
    GeneSpec("support_count", GeneType.INTEGER, layer=2, min_val=1, max_val=8, default=4),
    GeneSpec("subtype", GeneType.CATEGORICAL, layer=1,
             categories=["dining", "coffee", "side"], default="dining"),
    GeneSpec("symmetric", GeneType.BOOLEAN, layer=1, default=True),
    GeneSpec("family_name", GeneType.CATEGORICAL, layer=1,
             categories=["table_family"], default="table_family"),
]


def _genome(rng: random.Random | None = None, **overrides) -> Genome:
    rng = rng or random.Random(42)
    g = Genome.random_init(SIMPLE_CATALOG, rng)
    g.genes.update(overrides)
    return g


def _candidate(physics=0.7, aesthetic=0.6, novelty=0.5, valid=True, **gene_overrides):
    from core.evolution.candidate import Candidate
    g = _genome(**gene_overrides)
    return Candidate(
        genome=g,
        family="table_family",
        physics_score=physics,
        aesthetic_score=aesthetic,
        novelty_score=novelty,
        is_valid=valid,
    )


# ===========================================================================
# 1. Candidate
# ===========================================================================

class TestCandidate:
    def test_candidate_construction(self):
        from core.evolution.candidate import Candidate
        c = _candidate()
        assert c.genome is not None
        assert c.family == "table_family"
        assert 0.0 <= c.physics_score <= 1.0

    def test_combined_score_weighted(self):
        from core.evolution.candidate import Candidate
        c = _candidate(physics=0.8, aesthetic=0.6, novelty=0.4)
        score = c.combined_score(
            physics_weight=0.3,
            aesthetic_weight=0.5,
            novelty_weight=0.2,
        )
        expected = 0.8 * 0.3 + 0.6 * 0.5 + 0.4 * 0.2
        assert abs(score - expected) < 1e-6

    def test_invalid_candidate_zero_elite_score(self):
        from core.evolution.candidate import Candidate
        c = _candidate(valid=False)
        assert c.combined_score(0.3, 0.5, 0.2) == 0.0

    def test_candidate_serialisation_round_trip(self):
        from core.evolution.candidate import Candidate
        c = _candidate()
        d = c.to_dict()
        c2 = Candidate.from_dict(d)
        assert c2.genome.genome_id == c.genome.genome_id
        assert abs(c2.physics_score - c.physics_score) < 1e-9

    def test_candidate_human_boost(self):
        from core.evolution.candidate import Candidate
        c = _candidate(physics=0.5, aesthetic=0.5, novelty=0.5)
        score_before = c.combined_score(1 / 3, 1 / 3, 1 / 3)
        c.human_selected = True
        score_after = c.combined_score(1 / 3, 1 / 3, 1 / 3)
        assert score_after > score_before

    def test_candidate_unique_ids(self):
        from core.evolution.candidate import Candidate
        c1 = _candidate()
        c2 = _candidate()
        assert c1.candidate_id != c2.candidate_id


# ===========================================================================
# 2. Novelty
# ===========================================================================

class TestNovelty:
    def test_genome_distance_same_genome_zero(self):
        from core.novelty.novelty import genome_distance
        g = _genome()
        assert genome_distance(g, g, SIMPLE_CATALOG) == pytest.approx(0.0)

    def test_genome_distance_different_is_positive(self):
        from core.novelty.novelty import genome_distance
        rng = random.Random(1)
        g1 = _genome(rng, width=100.0, support_count=1)
        g2 = _genome(rng, width=500.0, support_count=8)
        assert genome_distance(g1, g2, SIMPLE_CATALOG) > 0.0

    def test_genome_distance_symmetric(self):
        from core.novelty.novelty import genome_distance
        rng = random.Random(7)
        g1, g2 = _genome(rng), _genome(rng)
        assert genome_distance(g1, g2, SIMPLE_CATALOG) == pytest.approx(
            genome_distance(g2, g1, SIMPLE_CATALOG)
        )

    def test_genome_distance_bounded_0_1(self):
        from core.novelty.novelty import genome_distance
        rng = random.Random(99)
        for _ in range(20):
            g1, g2 = _genome(rng), _genome(rng)
            d = genome_distance(g1, g2, SIMPLE_CATALOG)
            assert 0.0 <= d <= 1.0, f"distance {d} out of [0,1]"

    def test_compute_novelty_scores(self):
        from core.novelty.novelty import compute_novelty_scores
        rng = random.Random(5)
        population = [_genome(rng) for _ in range(10)]
        scores = compute_novelty_scores(population, SIMPLE_CATALOG, k=3)
        assert len(scores) == 10
        for s in scores:
            assert 0.0 <= s <= 1.0

    def test_novelty_scores_differ_across_diverse_population(self):
        from core.novelty.novelty import compute_novelty_scores
        rng = random.Random(11)
        # Two clusters: low width vs high width
        pop = [_genome(rng, width=100.0) for _ in range(5)]
        pop += [_genome(rng, width=490.0) for _ in range(5)]
        scores = compute_novelty_scores(pop, SIMPLE_CATALOG, k=3)
        # Each cluster member should have similar novelty (not all identical)
        assert len(set(round(s, 4) for s in scores)) > 1


# ===========================================================================
# 3. Selection
# ===========================================================================

class TestSelection:
    def _pop(self, n=10):
        return [_candidate(physics=random.random()) for _ in range(n)]

    def test_tournament_selection_returns_candidate(self):
        from core.selection.selection import tournament_select
        rng = random.Random(42)
        pop = self._pop()
        winner = tournament_select(pop, tournament_size=3, rng=rng,
                                   physics_weight=0.4, aesthetic_weight=0.4, novelty_weight=0.2)
        assert winner in pop

    def test_tournament_prefers_higher_score(self):
        from core.selection.selection import tournament_select
        rng = random.Random(0)
        best = _candidate(physics=1.0, aesthetic=1.0, novelty=1.0)
        rest = [_candidate(physics=0.0, aesthetic=0.0, novelty=0.0) for _ in range(9)]
        pop = rest + [best]
        winners = [
            tournament_select(pop, tournament_size=5, rng=rng,
                              physics_weight=1/3, aesthetic_weight=1/3, novelty_weight=1/3)
            for _ in range(30)
        ]
        assert winners.count(best) > 10

    def test_tournament_excludes_invalid(self):
        from core.selection.selection import tournament_select
        rng = random.Random(1)
        invalid = [_candidate(valid=False) for _ in range(5)]
        valid = [_candidate(physics=0.8) for _ in range(5)]
        pop = invalid + valid
        for _ in range(20):
            w = tournament_select(pop, tournament_size=3, rng=rng,
                                  physics_weight=1/3, aesthetic_weight=1/3, novelty_weight=1/3)
            assert w.is_valid

    def test_select_parents_returns_correct_count(self):
        from core.selection.selection import select_parents
        rng = random.Random(42)
        pop = self._pop(20)
        parents = select_parents(pop, n=8, tournament_size=3, rng=rng,
                                 physics_weight=1/3, aesthetic_weight=1/3, novelty_weight=1/3)
        assert len(parents) == 8

    def test_elites_are_top_k(self):
        from core.selection.selection import get_elites
        pop = [_candidate(physics=i / 10) for i in range(10)]
        elites = get_elites(pop, k=3, physics_weight=1.0, aesthetic_weight=0.0, novelty_weight=0.0)
        scores = [e.combined_score(1.0, 0.0, 0.0) for e in elites]
        assert scores == sorted(scores, reverse=True)
        assert len(elites) == 3

    def test_elites_only_valid(self):
        from core.selection.selection import get_elites
        pop = [_candidate(physics=0.9, valid=False) for _ in range(5)]
        pop += [_candidate(physics=0.5, valid=True) for _ in range(5)]
        elites = get_elites(pop, k=3, physics_weight=1.0, aesthetic_weight=0.0, novelty_weight=0.0)
        assert all(e.is_valid for e in elites)


# ===========================================================================
# 4. Mutation
# ===========================================================================

class TestMutation:
    def test_mutate_returns_new_genome(self):
        from core.mutation.mutation import mutate
        rng = random.Random(42)
        g = _genome()
        g2 = mutate(g, SIMPLE_CATALOG, mutation_rate=1.0, rng=rng)
        assert g2.genome_id != g.genome_id

    def test_mutate_rate_zero_leaves_values_same(self):
        from core.mutation.mutation import mutate
        rng = random.Random(42)
        g = _genome()
        original = deepcopy(g.genes)
        g2 = mutate(g, SIMPLE_CATALOG, mutation_rate=0.0, rng=rng)
        assert g2.genes == original

    def test_mutate_respects_bounds(self):
        from core.mutation.mutation import mutate
        rng = random.Random(7)
        for _ in range(50):
            g = _genome()
            g2 = mutate(g, SIMPLE_CATALOG, mutation_rate=1.0, rng=rng)
            assert g2.validate(SIMPLE_CATALOG)

    def test_mutate_continuous_changes_value(self):
        from core.mutation.mutation import mutate
        rng = random.Random(1)
        g = _genome()
        changed = False
        for _ in range(20):
            g2 = mutate(g, SIMPLE_CATALOG, mutation_rate=1.0, rng=rng)
            if g2.genes["width"] != g.genes["width"]:
                changed = True
                break
        assert changed

    def test_mutate_categorical_stays_valid(self):
        from core.mutation.mutation import mutate
        rng = random.Random(99)
        g = _genome()
        for _ in range(20):
            g2 = mutate(g, SIMPLE_CATALOG, mutation_rate=1.0, rng=rng)
            assert g2.genes["subtype"] in ["dining", "coffee", "side"]

    def test_mutate_boolean_can_flip(self):
        from core.mutation.mutation import mutate
        rng = random.Random(3)
        g = _genome()
        g.genes["symmetric"] = True
        flipped = False
        for _ in range(30):
            g2 = mutate(g, SIMPLE_CATALOG, mutation_rate=1.0, rng=rng)
            if g2.genes["symmetric"] is False:
                flipped = True
                break
        assert flipped


# ===========================================================================
# 5. Crossover
# ===========================================================================

class TestCrossover:
    def test_crossover_produces_two_children(self):
        from core.crossover.crossover import uniform_crossover
        rng = random.Random(42)
        p1, p2 = _genome(), _genome()
        c1, c2 = uniform_crossover(p1, p2, SIMPLE_CATALOG, rng=rng)
        assert c1.genome_id != p1.genome_id
        assert c2.genome_id != p2.genome_id

    def test_crossover_children_have_valid_genes(self):
        from core.crossover.crossover import uniform_crossover
        rng = random.Random(10)
        for _ in range(20):
            p1 = _genome(rng)
            p2 = _genome(rng)
            c1, c2 = uniform_crossover(p1, p2, SIMPLE_CATALOG, rng=rng)
            assert c1.validate(SIMPLE_CATALOG), f"c1 invalid: {c1.genes}"
            assert c2.validate(SIMPLE_CATALOG), f"c2 invalid: {c2.genes}"

    def test_crossover_genes_from_parents(self):
        from core.crossover.crossover import uniform_crossover
        rng = random.Random(0)
        p1 = _genome(rng, width=100.0)
        p2 = _genome(rng, width=500.0)
        c1, c2 = uniform_crossover(p1, p2, SIMPLE_CATALOG, rng=rng)
        assert c1.genes["width"] in (100.0, 500.0)
        assert c2.genes["width"] in (100.0, 500.0)

    def test_crossover_incompatible_families_raises(self):
        from core.crossover.crossover import uniform_crossover, CrossoverError
        rng = random.Random(42)
        p1 = _genome()
        p1.genes["family_name"] = "table_family"
        p2 = _genome()
        p2.genes["family_name"] = "lamp_family"
        with pytest.raises(CrossoverError):
            uniform_crossover(p1, p2, SIMPLE_CATALOG, rng=rng)

    def test_single_point_crossover_produces_valid_children(self):
        from core.crossover.crossover import single_point_crossover
        rng = random.Random(5)
        for _ in range(20):
            p1, p2 = _genome(rng), _genome(rng)
            p1.genes["family_name"] = "table_family"
            p2.genes["family_name"] = "table_family"
            c1, c2 = single_point_crossover(p1, p2, SIMPLE_CATALOG, rng=rng)
            assert c1.validate(SIMPLE_CATALOG)
            assert c2.validate(SIMPLE_CATALOG)


# ===========================================================================
# 6. Repair
# ===========================================================================

class TestRepair:
    def test_repair_clamps_out_of_range(self):
        from core.repair.repair import repair_genome
        g = _genome()
        g.genes["width"] = 9999.0  # way over max
        g.genes["support_count"] = -1  # under min
        repaired = repair_genome(g, SIMPLE_CATALOG)
        assert repaired.validate(SIMPLE_CATALOG)

    def test_repair_fixes_invalid_categorical(self):
        from core.repair.repair import repair_genome
        g = _genome()
        g.genes["subtype"] = "invalid_value"
        repaired = repair_genome(g, SIMPLE_CATALOG)
        assert repaired.genes["subtype"] in ["dining", "coffee", "side"]

    def test_repair_returns_new_genome(self):
        from core.repair.repair import repair_genome
        g = _genome()
        g.genes["width"] = 9999.0
        repaired = repair_genome(g, SIMPLE_CATALOG)
        assert repaired is not g

    def test_valid_genome_unchanged_by_repair(self):
        from core.repair.repair import repair_genome
        g = _genome()
        original = deepcopy(g.genes)
        repaired = repair_genome(g, SIMPLE_CATALOG)
        assert repaired.genes == original


# ===========================================================================
# 7. MAP-Elites Archive
# ===========================================================================

class TestMAPElitesArchive:
    def test_archive_insert_and_retrieve(self):
        from core.map_elites.archive import MAPElitesArchive
        archive = MAPElitesArchive(
            descriptor_keys=["support_count", "width"],
            bins_per_axis=5,
        )
        c = _candidate(physics=0.8)
        archive.try_insert(c)
        assert archive.size() >= 1

    def test_archive_replaces_weaker_candidate(self):
        from core.map_elites.archive import MAPElitesArchive
        archive = MAPElitesArchive(
            descriptor_keys=["support_count", "width"],
            bins_per_axis=5,
        )
        weak = _candidate(physics=0.2, support_count=4)
        strong = _candidate(physics=0.9, support_count=4)
        # Force same descriptor cell by setting same gene values
        weak.genome.genes["support_count"] = 4
        weak.genome.genes["width"] = 200.0
        strong.genome.genes["support_count"] = 4
        strong.genome.genes["width"] = 200.0
        archive.try_insert(weak)
        archive.try_insert(strong)
        best = archive.get_best()
        assert strong in best or any(
            c.candidate_id == strong.candidate_id for c in best
        )

    def test_archive_preserves_diversity(self):
        from core.map_elites.archive import MAPElitesArchive
        archive = MAPElitesArchive(
            descriptor_keys=["support_count", "width"],
            bins_per_axis=5,
        )
        rng = random.Random(42)
        for sc in range(1, 9):
            for w in [100.0, 200.0, 300.0, 400.0, 500.0]:
                c = _candidate(physics=rng.random(), support_count=sc)
                c.genome.genes["support_count"] = sc
                c.genome.genes["width"] = w
                archive.try_insert(c)
        assert archive.size() > 5

    def test_archive_get_random_sample(self):
        from core.map_elites.archive import MAPElitesArchive
        archive = MAPElitesArchive(
            descriptor_keys=["support_count", "width"],
            bins_per_axis=5,
        )
        rng = random.Random(1)
        for i in range(20):
            c = _candidate(support_count=(i % 8) + 1)
            c.genome.genes["support_count"] = (i % 8) + 1
            c.genome.genes["width"] = 100.0 + i * 20
            archive.try_insert(c)
        sample = archive.random_sample(n=5, rng=rng)
        assert 1 <= len(sample) <= 5

    def test_archive_ignores_invalid_candidates(self):
        from core.map_elites.archive import MAPElitesArchive
        archive = MAPElitesArchive(
            descriptor_keys=["support_count", "width"],
            bins_per_axis=5,
        )
        c = _candidate(valid=False)
        archive.try_insert(c)
        assert archive.size() == 0


# ===========================================================================
# 8. Island
# ===========================================================================

class TestIsland:
    def _island(self, pop_size=10):
        from core.leagues.island import Island
        rng = random.Random(42)
        population = [_candidate() for _ in range(pop_size)]
        return Island(
            island_id="i0",
            league_id="l0",
            population=population,
            catalog=SIMPLE_CATALOG,
            rng=rng,
            mutation_rate=0.3,
            crossover_rate=0.7,
        )

    def test_island_construction(self):
        island = self._island()
        assert island.island_id == "i0"
        assert len(island.population) == 10

    def test_island_step_returns_new_generation(self):
        from core.leagues.island import Island
        island = self._island()
        new_pop = island.step(
            n_offspring=5,
            physics_weight=0.4,
            aesthetic_weight=0.4,
            novelty_weight=0.2,
        )
        assert len(new_pop) > 0
        # All should be Candidate instances
        from core.evolution.candidate import Candidate
        assert all(isinstance(c, Candidate) for c in new_pop)

    def test_island_step_offspring_are_valid_genomes(self):
        island = self._island()
        new_pop = island.step(
            n_offspring=5,
            physics_weight=1/3,
            aesthetic_weight=1/3,
            novelty_weight=1/3,
        )
        for c in new_pop:
            assert c.genome.validate(SIMPLE_CATALOG)

    def test_island_receive_migrants(self):
        island = self._island()
        migrants = [_candidate() for _ in range(3)]
        island.receive_migrants(migrants)
        # Population should include migrants
        ids = {c.candidate_id for c in island.population}
        for m in migrants:
            assert m.candidate_id in ids

    def test_island_get_emigrants(self):
        from core.leagues.island import Island
        rng = random.Random(7)
        population = [_candidate(physics=i / 10) for i in range(10)]
        island = Island(
            island_id="i1",
            league_id="l0",
            population=population,
            catalog=SIMPLE_CATALOG,
            rng=rng,
            mutation_rate=0.3,
            crossover_rate=0.7,
        )
        emigrants = island.get_emigrants(n=3,
                                         physics_weight=1.0,
                                         aesthetic_weight=0.0,
                                         novelty_weight=0.0)
        assert len(emigrants) == 3
        # Should be the top scorers
        scores = [e.combined_score(1.0, 0.0, 0.0) for e in emigrants]
        assert scores == sorted(scores, reverse=True)


# ===========================================================================
# 9. League
# ===========================================================================

class TestLeague:
    def _league(self, n_islands=2, pop_per_island=8):
        from core.leagues.league import League
        from core.leagues.island import Island
        rng = random.Random(42)
        islands = []
        for i in range(n_islands):
            pop = [_candidate() for _ in range(pop_per_island)]
            islands.append(Island(
                island_id=f"i{i}",
                league_id="l0",
                population=pop,
                catalog=SIMPLE_CATALOG,
                rng=random.Random(i),
                mutation_rate=0.3,
                crossover_rate=0.7,
            ))
        return League(
            league_id="l0",
            islands=islands,
            migration_rate=0.2,
            migration_interval=2,
        )

    def test_league_construction(self):
        league = self._league()
        assert league.league_id == "l0"
        assert len(league.islands) == 2

    def test_league_step_advances_generation(self):
        league = self._league()
        gen_before = league.generation
        league.step(
            n_offspring_per_island=4,
            physics_weight=1/3,
            aesthetic_weight=1/3,
            novelty_weight=1/3,
        )
        assert league.generation == gen_before + 1

    def test_league_migration_occurs_at_interval(self):
        league = self._league()
        ids_before = {
            island.island_id: {c.candidate_id for c in island.population}
            for island in league.islands
        }
        # Run for migration_interval steps
        for _ in range(league.migration_interval):
            league.step(
                n_offspring_per_island=4,
                physics_weight=1/3,
                aesthetic_weight=1/3,
                novelty_weight=1/3,
            )
        # After migration, at least one island should have new candidates
        changed = False
        for island in league.islands:
            new_ids = {c.candidate_id for c in island.population}
            if new_ids != ids_before[island.island_id]:
                changed = True
                break
        assert changed

    def test_league_leaderboard_returns_top_k(self):
        league = self._league()
        top = league.leaderboard(k=3,
                                 physics_weight=1.0,
                                 aesthetic_weight=0.0,
                                 novelty_weight=0.0)
        assert len(top) <= 3
        from core.evolution.candidate import Candidate
        assert all(isinstance(c, Candidate) for c in top)

    def test_league_leaderboard_sorted(self):
        league = self._league()
        top = league.leaderboard(k=5,
                                 physics_weight=1.0,
                                 aesthetic_weight=0.0,
                                 novelty_weight=0.0)
        scores = [c.combined_score(1.0, 0.0, 0.0) for c in top]
        assert scores == sorted(scores, reverse=True)


# ===========================================================================
# 10. Engine (run loop orchestrator — thin integration test)
# ===========================================================================

class TestEngine:
    def _engine(self):
        from core.evolution.engine import EvolutionEngine
        from core.leagues.island import Island
        from core.leagues.league import League

        rng = random.Random(42)
        islands = []
        for i in range(2):
            pop = [_candidate() for _ in range(8)]
            islands.append(Island(
                island_id=f"i{i}",
                league_id="l0",
                population=pop,
                catalog=SIMPLE_CATALOG,
                rng=random.Random(i + 10),
                mutation_rate=0.3,
                crossover_rate=0.7,
            ))
        league = League(
            league_id="l0",
            islands=islands,
            migration_rate=0.2,
            migration_interval=2,
        )
        return EvolutionEngine(
            leagues=[league],
            catalog=SIMPLE_CATALOG,
            physics_weight=1/3,
            aesthetic_weight=1/3,
            novelty_weight=1/3,
            n_offspring_per_island=4,
        )

    def test_engine_construction(self):
        engine = self._engine()
        assert engine.generation == 0

    def test_engine_step_increments_generation(self):
        engine = self._engine()
        engine.step()
        assert engine.generation == 1

    def test_engine_run_n_generations(self):
        engine = self._engine()
        engine.run(n_generations=3)
        assert engine.generation == 3

    def test_engine_get_all_candidates(self):
        from core.evolution.candidate import Candidate
        engine = self._engine()
        engine.run(n_generations=2)
        all_c = engine.get_all_candidates()
        assert len(all_c) > 0
        assert all(isinstance(c, Candidate) for c in all_c)

    def test_engine_best_candidates(self):
        engine = self._engine()
        engine.run(n_generations=2)
        best = engine.best_candidates(k=3)
        assert len(best) <= 3
        scores = [c.combined_score(1/3, 1/3, 1/3) for c in best]
        assert scores == sorted(scores, reverse=True)

    def test_engine_step_callback(self):
        engine = self._engine()
        calls = []
        engine.on_generation_complete = lambda gen, candidates: calls.append(gen)
        engine.run(n_generations=3)
        assert calls == [1, 2, 3]
