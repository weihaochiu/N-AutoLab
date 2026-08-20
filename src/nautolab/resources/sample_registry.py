"""Sample registry."""

from nautolab.core import ResourceInUseError, Sample

from ._registry import ResourceRegistry


class SampleRegistry(ResourceRegistry[Sample]):
    """Authoritative lookup collection for samples."""

    resource_label = "sample"

    def remove(self, resource_id: str) -> Sample:
        """Remove only an unplaced sample resource."""
        sample = self.get(resource_id)
        if sample.current_location is not None:
            raise ResourceInUseError(
                f"cannot remove sample {resource_id!r}: it is currently placed in "
                f"slot {sample.current_location!r}; remove/unplace the sample first"
            )
        return super().remove(resource_id)
