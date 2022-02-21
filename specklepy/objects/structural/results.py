from typing import List

from ..base import Base
from ..geometry import *
from .loading import *
from .geometry import *
from .analysis import Model

STRUCTURAL_RESULTS = "Objects.Structural.Results."


class Result(Base, speckle_type=STRUCTURAL_RESULTS + "Result"):
    resultCase: Base = None
    permutation: str = None
    description: str = None


class ResultSet1D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet1D"):
    results1D: List


class Result1D(Result, speckle_type=STRUCTURAL_RESULTS + "Result1D"):
    element: Element1D = None
    position: float = 0.0
    dispX: float = 0.0
    dispY: float = 0.0
    dispZ: float = 0.0
    rotXX: float = 0.0
    rotYY: float = 0.0
    rotZZ: float = 0.0
    forceX: float = 0.0
    forceY: float = 0.0
    forceZ: float = 0.0
    momentXX: float = 0.0
    momentYY: float = 0.0
    momentZZ: float = 0.0
    axialStress: float = 0.0
    shearStressY: float = 0.0
    shearStressZ: float = 0.0
    bendingStressYPos: float = 0.0
    bendingStressYNeg: float = 0.0
    bendingStressZPos: float = 0.0
    bendingStressZNeg: float = 0.0
    combinedStressMax: float = 0.0
    combinedStressMin: float = 0.0


class ResultSet2D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet2D"):
    results2D: List


class Result2D(Result, speckle_type=STRUCTURAL_RESULTS + "Result2D"):
    element: Element2D = None
    position: List
    dispX: float = 0.0
    dispY: float = 0.0
    dispZ: float = 0.0
    forceXX: float = 0.0
    forceYY: float = 0.0
    forceXY: float = 0.0
    momentXX: float = 0.0
    momentYY: float = 0.0
    momentXY: float = 0.0
    shearX: float = 0.0
    shearY: float = 0.0
    stressTopXX: float = 0.0
    stressTopYY: float = 0.0
    stressTopZZ: float = 0.0
    stressTopXY: float = 0.0
    stressTopYZ: float = 0.0
    stressTopZX: float = 0.0
    stressMidXX: float = 0.0
    stressMidYY: float = 0.0
    stressMidZZ: float = 0.0
    stressMidXY: float = 0.0
    stressMidYZ: float = 0.0
    stressMidZX: float = 0.0
    stressBotXX: float = 0.0
    stressBotYY: float = 0.0
    stressBotZZ: float = 0.0
    stressBotXY: float = 0.0
    stressBotYZ: float = 0.0
    stressBotZX: float = 0.0


class ResultSet3D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet3D"):
    results3D: List


class Result3D(Result, speckle_type=STRUCTURAL_RESULTS + "Result3D"):
    element: Element3D = None
    position: List
    dispX: float = 0.0
    dispY: float = 0.0
    dispZ: float = 0.0
    stressXX: float = 0.0
    stressYY: float = 0.0
    stressZZ: float = 0.0
    stressXY: float = 0.0
    stressYZ: float = 0.0
    stressZX: float = 0.0


class ResultGlobal(Result, speckle_type=STRUCTURAL_RESULTS + "ResultGlobal"):
    model: Model = None
    loadX: float = 0.0
    loadY: float = 0.0
    loadZ: float = 0.0
    loadXX: float = 0.0
    loadYY: float = 0.0
    loadZZ: float = 0.0
    reactionX: float = 0.0
    reactionY: float = 0.0
    reactionZ: float = 0.0
    reactionXX: float = 0.0
    reactionYY: float = 0.0
    reactionZZ: float = 0.0
    mode: float = 0.0
    frequency: float = 0.0
    loadFactor: float = 0.0
    modalStiffness: float = 0.0
    modalGeoStiffness: float = 0.0
    effMassX: float = 0.0
    effMassY: float = 0.0
    effMassZ: float = 0.0
    effMassXX: float = 0.0
    effMassYY: float = 0.0
    effMassZZ: float = 0.0


class ResultSetNode(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSetNode"):
    resultsNode: List


class ResultNode(Result, speckle_type=STRUCTURAL_RESULTS + " ResultNode"):
    node: Node = None
    dispX: float = 0.0
    dispY: float = 0.0
    dispZ: float = 0.0
    rotXX: float = 0.0
    rotYY: float = 0.0
    rotZZ: float = 0.0
    reactionX: float = 0.0
    reactionY: float = 0.0
    reactionZ: float = 0.0
    reactionXX: float = 0.0
    reactionYY: float = 0.0
    reactionZZ: float = 0.0
    constraintX: float = 0.0
    constraintY: float = 0.0
    constraintZ: float = 0.0
    constraintXX: float = 0.0
    constraintYY: float = 0.0
    constraintZZ: float = 0.0
    velX: float = 0.0
    velY: float = 0.0
    velZ: float = 0.0
    velXX: float = 0.0
    velYY: float = 0.0
    velZZ: float = 0.0
    accX: float = 0.0
    accY: float = 0.0
    accZ: float = 0.0
    accXX: float = 0.0
    accYY: float = 0.0
    accZZ: float = 0.0


class ResultSetAll(Base, speckle_type=None):
    resultSet1D: ResultSet1D = None
    resultSet2D: ResultSet2D = None
    resultSet3D: ResultSet3D = None
    resultsGlobal: ResultGlobal = None
    resultsNode: ResultSetNode = None
