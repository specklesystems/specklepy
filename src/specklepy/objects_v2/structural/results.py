from typing import List, Optional

from specklepy.objects.base import Base
from specklepy.objects.structural.analysis import Model
from specklepy.objects.structural.geometry import Element1D, Element2D, Element3D, Node

STRUCTURAL_RESULTS = "Objects.Structural.Results."


class Result(Base, speckle_type=STRUCTURAL_RESULTS + "Result"):
    resultCase: Optional[Base] = None
    permutation: Optional[str] = None
    description: Optional[str] = None


class ResultSet1D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet1D"):
    results1D: List


class Result1D(Result, speckle_type=STRUCTURAL_RESULTS + "Result1D"):
    element: Optional[Element1D] = None
    position: Optional[float] = None
    dispX: Optional[float] = None
    dispY: Optional[float] = None
    dispZ: Optional[float] = None
    rotXX: Optional[float] = None
    rotYY: Optional[float] = None
    rotZZ: Optional[float] = None
    forceX: Optional[float] = None
    forceY: Optional[float] = None
    forceZ: Optional[float] = None
    momentXX: Optional[float] = None
    momentYY: Optional[float] = None
    momentZZ: Optional[float] = None
    axialStress: Optional[float] = None
    shearStressY: Optional[float] = None
    shearStressZ: Optional[float] = None
    bendingStressYPos: Optional[float] = None
    bendingStressYNeg: Optional[float] = None
    bendingStressZPos: Optional[float] = None
    bendingStressZNeg: Optional[float] = None
    combinedStressMax: Optional[float] = None
    combinedStressMin: Optional[float] = None


class ResultSet2D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet2D"):
    results2D: List


class Result2D(Result, speckle_type=STRUCTURAL_RESULTS + "Result2D"):
    element: Optional[Element2D] = None
    position: List
    dispX: Optional[float] = None
    dispY: Optional[float] = None
    dispZ: Optional[float] = None
    forceXX: Optional[float] = None
    forceYY: Optional[float] = None
    forceXY: Optional[float] = None
    momentXX: Optional[float] = None
    momentYY: Optional[float] = None
    momentXY: Optional[float] = None
    shearX: Optional[float] = None
    shearY: Optional[float] = None
    stressTopXX: Optional[float] = None
    stressTopYY: Optional[float] = None
    stressTopZZ: Optional[float] = None
    stressTopXY: Optional[float] = None
    stressTopYZ: Optional[float] = None
    stressTopZX: Optional[float] = None
    stressMidXX: Optional[float] = None
    stressMidYY: Optional[float] = None
    stressMidZZ: Optional[float] = None
    stressMidXY: Optional[float] = None
    stressMidYZ: Optional[float] = None
    stressMidZX: Optional[float] = None
    stressBotXX: Optional[float] = None
    stressBotYY: Optional[float] = None
    stressBotZZ: Optional[float] = None
    stressBotXY: Optional[float] = None
    stressBotYZ: Optional[float] = None
    stressBotZX: Optional[float] = None


class ResultSet3D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet3D"):
    results3D: List


class Result3D(Result, speckle_type=STRUCTURAL_RESULTS + "Result3D"):
    element: Optional[Element3D] = None
    position: List
    dispX: Optional[float] = None
    dispY: Optional[float] = None
    dispZ: Optional[float] = None
    stressXX: Optional[float] = None
    stressYY: Optional[float] = None
    stressZZ: Optional[float] = None
    stressXY: Optional[float] = None
    stressYZ: Optional[float] = None
    stressZX: Optional[float] = None


class ResultGlobal(Result, speckle_type=STRUCTURAL_RESULTS + "ResultGlobal"):
    model: Optional[Model] = None
    loadX: Optional[float] = None
    loadY: Optional[float] = None
    loadZ: Optional[float] = None
    loadXX: Optional[float] = None
    loadYY: Optional[float] = None
    loadZZ: Optional[float] = None
    reactionX: Optional[float] = None
    reactionY: Optional[float] = None
    reactionZ: Optional[float] = None
    reactionXX: Optional[float] = None
    reactionYY: Optional[float] = None
    reactionZZ: Optional[float] = None
    mode: Optional[float] = None
    frequency: Optional[float] = None
    loadFactor: Optional[float] = None
    modalStiffness: Optional[float] = None
    modalGeoStiffness: Optional[float] = None
    effMassX: Optional[float] = None
    effMassY: Optional[float] = None
    effMassZ: Optional[float] = None
    effMassXX: Optional[float] = None
    effMassYY: Optional[float] = None
    effMassZZ: Optional[float] = None


class ResultSetNode(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSetNode"):
    resultsNode: List


class ResultNode(Result, speckle_type=STRUCTURAL_RESULTS + " ResultNode"):
    node: Optional[Node] = None
    dispX: Optional[float] = None
    dispY: Optional[float] = None
    dispZ: Optional[float] = None
    rotXX: Optional[float] = None
    rotYY: Optional[float] = None
    rotZZ: Optional[float] = None
    reactionX: Optional[float] = None
    reactionY: Optional[float] = None
    reactionZ: Optional[float] = None
    reactionXX: Optional[float] = None
    reactionYY: Optional[float] = None
    reactionZZ: Optional[float] = None
    constraintX: Optional[float] = None
    constraintY: Optional[float] = None
    constraintZ: Optional[float] = None
    constraintXX: Optional[float] = None
    constraintYY: Optional[float] = None
    constraintZZ: Optional[float] = None
    velX: Optional[float] = None
    velY: Optional[float] = None
    velZ: Optional[float] = None
    velXX: Optional[float] = None
    velYY: Optional[float] = None
    velZZ: Optional[float] = None
    accX: Optional[float] = None
    accY: Optional[float] = None
    accZ: Optional[float] = None
    accXX: Optional[float] = None
    accYY: Optional[float] = None
    accZZ: Optional[float] = None


class ResultSetAll(Base, speckle_type=None):
    resultSet1D: Optional[ResultSet1D] = None
    resultSet2D: Optional[ResultSet2D] = None
    resultSet3D: Optional[ResultSet3D] = None
    resultsGlobal: Optional[ResultGlobal] = None
    resultsNode: Optional[ResultSetNode] = None
