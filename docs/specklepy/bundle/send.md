# Sending bundle versions

`BundleBuilder` is the authoring API for the new Speckle object model: you describe
objects, their properties and geometry, and the relationships between them, and
`operations.send3` publishes the result as a new version over the `/api/v2` rail.
Requires the `bundle` extra:

```
pip install "specklepy[bundle]"
```

## Authoring

```python
from specklepy.api import operations
from specklepy.api.credentials import get_default_account
from specklepy.bundle import BundleBuilder, Producer
from specklepy.objects.geometry import Mesh

b = BundleBuilder(Producer(slug="my-script", version="1.0"), units="m")

walls = b.get_or_add_container_path(["Level 1", "Walls"], subtype="Category")
concrete = b.get_or_add_material("concrete", "Concrete", argb=-8355712, roughness=0.8)
level = b.get_or_add_level("L1", "Level 1", elevation=0.0)

wall = b.get_or_add_object("wall-1").set_properties(
    {"Constraints": {"Base Offset": 0.5}},
    name="Basic Wall",
    speckle_type="Objects.Data.DataObject",
    source_type="Walls",
)
wall.collection = walls
wall.level = level
wall.add_geometry(Mesh(vertices=[...], faces=[...], units="m")).material = concrete

door = b.get_or_add_object("door-1").set_properties({"Width": 0.9}, name="Door")
door.collection = walls
door.host = wall
door.parent = wall

chair = b.get_or_add_definition(
    "def-chair", "Chair", lambda d: d.add_geometry(chair_mesh)
)
b.get_or_add_object("chair-1").place(chair, transform)  # 16 row-major doubles

result = operations.send3(get_default_account(), project_id, model_id, b)
print(result.version_id, result.bundle_reference)
```

Rules, mirroring the .NET `BundleBuilder`:

- `get_or_add_*` interns a node by key: the same key returns the same handle and writes
  nothing; the same key with different attributes raises.
- `add_*` appends a row every call (geometry, model properties, camera views).
- Property setters and verbs (`wall.level = …`, `door.host = …`, `place`, `connect_to`)
  emit one edge each and cannot be retracted; assigning `None` before any edge is a no-op.
- `set_properties` writes an object's rows once; objects can be referenced before they
  are described.
- `build()` (called by `send3`) injects a default scene view grouping by collection when
  none was declared.

Definitions with members that own their properties use `add_member`,
`add_member_placement` and `add_existing_geometry`; nested placements use `place_nested`.

## `operations.send3`

`send3(account, project_id, model_id, builder, options=None)` takes an optional
[`SendOptions`][specklepy.bundle.send.SendOptions] (`message`, `file_name`,
`file_size_bytes`, `max_idle_timeout_seconds`, `keep_files`). It creates the model ingestion (the server reserves the version id), builds and
re-keys the bundle files to that id, uploads them, and returns a
[`SendResult`][specklepy.bundle.send.SendResult]. The version becomes visible when the
server finishes ingesting; poll `client.version.get` for it. The builder is finished by
the call and cannot be reused. On failure the ingestion is marked failed and the error
re-raised.

## API

::: specklepy.bundle.builder
    options:
      members:
        - BundleBuilder
        - BundleFiles
        - BundleObject
        - BundleDefinition
        - BundleGeometry
        - BundleContainer
        - BundleLevel
        - BundleMaterial
        - BundleColor
        - BundleInstance

::: specklepy.bundle.send.SendOptions

::: specklepy.bundle.send.SendResult
