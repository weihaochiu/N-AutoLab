"""Sample registry."""

from nautolab.core import Sample

from ._registry import ResourceRegistry


class SampleRegistry(ResourceRegistry[Sample]):
    """Authoritative lookup collection for samples."""

    resource_label = "sample"
