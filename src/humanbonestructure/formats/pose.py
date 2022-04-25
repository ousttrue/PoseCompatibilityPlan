from typing import NamedTuple, Optional, List, Dict, Set, Tuple
import abc
import glm
from .transform import Transform
from .humanoid_bones import HumanoidBone, HumanoidBodyParts
from ..scene.node import Node


class BonePose(NamedTuple):
    name: str
    humanoid_bone: Optional[HumanoidBone]
    transform: Transform


class Pose:
    def __init__(self, name: str):
        self.name = name
        self.bones: List[BonePose] = []
        self._parts: Dict[HumanoidBodyParts, bool] = {
        }

    def __str__(self) -> str:
        return f'{self.name}: {len(self.bones)}bones'

    def get_parts(self, part: HumanoidBodyParts) -> bool:
        value = self._parts.get(part)
        if not isinstance(value, bool):
            def has_part(bone: BonePose) -> bool:
                if not bone.humanoid_bone:
                    return False
                return bone.humanoid_bone.get_part() == part
            value = any(has_part(bone) for bone in self.bones)
            self._parts[part] = value
        return value

    def to_json(self, root: Node) -> Dict[str, Tuple[float, float, float, float]]:

        node_map = {node.humanoid_bone: node for node,
                    _ in root.traverse_node_and_parent() if node.humanoid_bone and node.humanoid_bone != HumanoidBone.endSite}

        def float4(q) -> Tuple[float, float, float, float]:
            return (q.x, q.y, q.z, q.w)
        bone_map: Dict[str, Tuple[float, float, float, float]] = {}
        for bone in self.bones:
            assert bone.humanoid_bone
            node = node_map[bone.humanoid_bone]
            if node and node.pose:
                q = glm.inverse(node.pose.rotation) * bone.transform.rotation
                bone_map[bone.humanoid_bone.name] = float4(q)

        return bone_map

    @staticmethod
    def from_json(name: str, bone_map: Dict[str, Tuple[float, float, float, float]]) -> 'Pose':
        pose = Pose(name)
        for k, v in bone_map.items():
            x, y, z, w = v
            pose.bones.append(
                BonePose(k, HumanoidBone(k), Transform.from_rotation(glm.quat(w, x, y, z))))
        return pose


class Motion(abc.ABC):
    def __init__(self, name: str) -> None:
        self.name = name
        self._parts_cache = None

    def get_humanboneparts(self) -> Set[HumanoidBodyParts]:
        if self._parts_cache is None:
            self._parts_cache = set(bone.get_part()
                                    for bone in self.get_humanbones())
        return self._parts_cache

    @ abc.abstractmethod
    def get_humanbones(self) -> Set[HumanoidBone]:
        raise NotImplementedError()

    @ abc.abstractmethod
    def get_current_pose(self) -> Pose:
        raise NotImplementedError()

    def start(self):
        pass

    def stop(self):
        pass


class Empty(Motion):
    def __init__(self) -> None:
        super().__init__('__empty__')
        self.pose = Pose(self.name)

    def get_humanbones(self) -> Set[HumanoidBone]:
        return set()

    def get_current_pose(self) -> Pose:
        return self.pose
