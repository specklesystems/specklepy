# Receiving bundle versions

Versions created with the new Speckle object model are *bundle-only*: instead of an object
graph they carry a bundle reference (`bundle.<projectId>.<modelId>.<versionId>`) in
`Version.referencedObject`, and their data lives in parquet artifacts served by the
`/api/v2` rail. Receiving one needs the `bundle` extra:

```
pip install "specklepy[bundle]"
```

## `operations.receive3`

```python
from specklepy.api import operations
from specklepy.api.credentials import get_default_account

account = get_default_account()
with operations.receive3(account, project_id, model_id, version_id) as model:
    for obj in model.objects_with("Constraints.Base Offset"):
        print(obj.application_id, obj["Constraints.Base Offset"], obj.level.name)

    wall = model.object_by_application_id("wall-1")
    for geometry in wall.geometries:  # placements already composed
        mesh = geometry.decode_mesh()
        material = geometry.effective_material
```

The returned [`Model`][specklepy.bundle.model.Model] owns the downloaded files until it is
closed (leave the `with` block, or call `close()`); parsed data stays usable afterwards.
Geometry is parsed from disk on first access — pass `include_geometry=False` to skip
downloading it entirely.

Properties are read straight from the bundle's columnar storage: `obj.properties` is a
read-only mapping of dotted paths (`"Constraints.Base Offset"`), `obj["path"]` resolves
instance → type → root scalar, and `model.objects_with(path)` scans one column across the
whole model.

## Legacy `operations.receive`

`operations.receive(obj_id, remote_transport, ...)` detects a bundle reference and returns
the same data projected onto the classic `Collection` / `DataObject` tree
(`Model.to_base()`): objects keyed by `applicationId`, nested `properties`,
`renderMaterialProxies` and `instanceDefinitionProxies` on the root, `version = 4`. It needs
an authenticated `ServerTransport` for the reference's project.

## API

::: specklepy.bundle.model
    options:
      members:
        - Model
        - ModelObject
        - ModelGeometry
        - ModelNode
        - ModelContainer
        - ModelLevel
        - ModelMaterial
        - ModelColor
        - ModelDefinition
        - ModelInstance
