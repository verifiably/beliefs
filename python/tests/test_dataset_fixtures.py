"""The seed-based dataset fixtures slice 5 migrates the corpus onto (design §8.2)."""

import pytest
from dataset_fixtures import dataset_ref, digest_for, pinned, pinned_for

from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address


def test_a_seed_gives_one_deterministic_pinned_declaration():
    assert pinned("raw") == pinned("raw")
    assert pinned("raw") != pinned("derived")
    assert pinned("raw") == [{"name": "matrix", "digest": digest_for("raw")}]
    assert digest_for("raw").startswith("sha256:") and len(digest_for("raw")) == len("sha256:") + 64


def test_dataset_ref_is_the_fold_over_the_pinned_declaration():
    declaration = DatasetDeclaration(resources=(ResourceDeclaration(name="matrix", digest=digest_for("raw")),))
    assert dataset_ref("raw") == dataset_address(declaration)
    assert dataset_ref("raw").startswith("dataset:sha256:")


def test_pinned_for_answers_a_ref_minted_by_dataset_ref_and_refuses_a_stranger():
    ref = dataset_ref("lineage-left")
    assert pinned_for(ref) == pinned("lineage-left")
    with pytest.raises(KeyError):
        pinned_for("dataset:never-minted")
