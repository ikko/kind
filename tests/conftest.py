import threading

import pytest

from kind.builtin import apply_builtins
from kind.builtin.avl_tree import AVLTree
from kind.core import mixinability
from kind.core.base_kind import BaseKind
from kind.core.kind import Kind


@pytest.fixture(params=["asyncio", "trio"])
def anyio_backend(request):
    """Every anyio test runs on both backends."""
    return request.param


@pytest.fixture(scope='session', autouse=True)
def apply_builtins_for_session():
    apply_builtins()


def _fresh_pool() -> None:
    """Forgets every Kind: a new pool and creation order (existing objects live on, unpooled)."""
    BaseKind._pool = {}
    BaseKind._numbered = AVLTree()
    BaseKind.max_kinds = None
    for cls in (Kind, *Kind.__subclasses__()):
        if "max_kinds" in vars(cls):
            delattr(cls, "max_kinds")
    BaseKind._auto_counter = 0
    BaseKind._write_cursor = 0.0
    BaseKind._lock = threading.RLock()


@pytest.fixture(autouse=True)
def isolated_kinds():
    """Every test starts with an empty pool, a fresh creation order and an unlocked mixin registry."""
    _fresh_pool()
    mixinability._unlock_mixins_for_testing()
    registry = mixinability._snapshot_for_testing()
    yield
    mixinability._restore_for_testing(registry)
    mixinability._unlock_mixins_for_testing()


@pytest.fixture
def reset_pool():
    """Call it mid-test to rebuild a graph from serialized text alone."""
    return _fresh_pool



@pytest.fixture(scope='function')
def kind_fixture():

    # Define a set of core bioinformatics terms for nodes
    core_nodes = [
        "Gene", "Protein", "Metabolite", "Pathway", "Disease", "Drug",
        "Cell", "Tissue", "Organism", "SNP", "Transcription Factor",
        "Enzyme", "Reaction", "Chromosome", "Phenotype", "Experiment",
        "Data Set", "Algorithm", "Network", "Interaction", "Regulation",
        "Expression", "Mutation", "Binding", "Activation", "Inhibition",
        "Sequence", "Structure", "Function", "Ontology", "Annotation"
    ]

    # Create Kind instances for core nodes
    kinds = {name: Kind(name) for name in core_nodes}

    # Establish parent-child relationships (tree-like structure)
    kinds["Gene"].append(kinds["Protein"])
    kinds["Protein"].append(kinds["Enzyme"])
    kinds["Enzyme"].append(kinds["Reaction"])
    kinds["Reaction"].append(kinds["Metabolite"])
    kinds["Gene"].append(kinds["Transcription Factor"])
    kinds["Transcription Factor"].append(kinds["Regulation"])
    kinds["Regulation"].append(kinds["Expression"])
    kinds["Protein"].append(kinds["Structure"])
    kinds["Structure"].append(kinds["Function"])
    kinds["Gene"].append(kinds["SNP"])
    kinds["SNP"].append(kinds["Disease"])
    kinds["Disease"].append(kinds["Phenotype"])
    kinds["Drug"].append(kinds["Disease"])
    kinds["Cell"].append(kinds["Tissue"])
    kinds["Tissue"].append(kinds["Organism"])
    kinds["Experiment"].append(kinds["Data Set"])
    kinds["Data Set"].append(kinds["Algorithm"])
    kinds["Algorithm"].append(kinds["Network"])
    kinds["Network"].append(kinds["Interaction"])
    kinds["Interaction"].append(kinds["Binding"])
    kinds["Binding"].append(kinds["Activation"])
    kinds["Activation"].append(kinds["Inhibition"])
    kinds["Sequence"].append(kinds["Gene"])
    kinds["Ontology"].append(kinds["Annotation"])

    # Establish custom relationships (graph-like structure)
    kinds["Protein"].relate(kinds["Drug"], how="targets")
    kinds["Gene"].relate(kinds["Disease"], how="associated_with")
    kinds["Metabolite"].relate(kinds["Pathway"], how="participates_in")
    kinds["Pathway"].relate(kinds["Regulation"], how="regulated_by")
    kinds["Protein"].relate(kinds["Protein"], how="interacts_with") # Self-loop for PPI
    kinds["Gene"].relate(kinds["Gene"], how="co_expresses_with")
    kinds["Drug"].relate(kinds["Enzyme"], how="inhibits")
    kinds["Disease"].relate(kinds["Organism"], how="affects")
    kinds["Experiment"].relate(kinds["Phenotype"], how="measures")
    kinds["Algorithm"].relate(kinds["Network"], how="analyzes")
    kinds["Network"].relate(kinds["Interaction"], how="contains")
    kinds["Ontology"].relate(kinds["Gene"], how="annotates")
    kinds["Annotation"].relate(kinds["Protein"], how="describes")
    kinds["Chromosome"].relate(kinds["Gene"], how="contains")
    kinds["SNP"].relate(kinds["Gene"], how="located_in")
    kinds["Cell"].relate(kinds["Protein"], how="expresses")
    kinds["Tissue"].relate(kinds["Cell"], how="composed_of")
    kinds["Organism"].relate(kinds["Tissue"], how="has_tissue")
    kinds["Sequence"].relate(kinds["Structure"], how="determines")
    kinds["Function"].relate(kinds["Protein"], how="performed_by")

    # Add some more complex relationships or cycles
    kinds["Disease"].relate(kinds["Drug"], how="treated_by") # Bidirectional
    kinds["Drug"].relate(kinds["Disease"], how="treats")

    # Ensure at least 30 nodes are interconnected
    # The current setup creates 30 unique kinds and establishes many connections.
    # The exact number of interconnections will depend on the append/relate calls.
    # We can verify the total number of kinds created by checking Kind._pool
    assert len(Kind._pool) >= 30, "Fixture did not create at least 30 unique kinds."
    print(f"DEBUG: kind_fixture created {len(Kind._pool)} kinds in pool.")
    if "Gene" in kinds:
        gene_root = kinds["Gene"]
        reachable_from_gene = gene_root.graph()
        print(f"DEBUG: {len(reachable_from_gene)} kinds reachable from 'Gene'.")

    yield kinds

