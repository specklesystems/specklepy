from specklepy.objects.geometry import Mesh
from specklepy.objects.other import RenderMaterial
from specklepy.objects.proxies import RenderMaterialProxy


class RenderMaterialProxyManager:
    def __init__(self):
        self._render_material_proxies: dict[str, RenderMaterialProxy] = {}

    @property
    def render_material_proxies(self):
        return self._render_material_proxies

    def add_mesh_material_mapping(
        self, render_material: RenderMaterial, mesh: Mesh
    ) -> None:
        material_id = render_material.applicationId
        assert material_id is not None
        mesh_id = mesh.applicationId
        assert mesh_id is not None

        proxy = self._render_material_proxies.get(material_id, None)
        if proxy is not None:
            proxy.objects.append(mesh_id)
        else:
            self._render_material_proxies[material_id] = RenderMaterialProxy(
                objects=[mesh_id], value=render_material
            )
