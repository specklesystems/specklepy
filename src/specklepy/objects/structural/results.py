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
    position: float = None
    dispX: float = None
    dispY: float = None
    dispZ: float = None
    rotXX: float = None
    rotYY: float = None
    rotZZ: float = None
    forceX: float = None
    forceY: float = None
    forceZ: float = None
    momentXX: float = None
    momentYY: float = None
    momentZZ: float = None
    axialStress: float = None
    shearStressY: float = None
    shearStressZ: float = None
    bendingStressYPos: float = None
    bendingStressYNeg: float = None
    bendingStressZPos: float = None
    bendingStressZNeg: float = None
    combinedStressMax: float = None
    combinedStressMin: float = None


class ResultSet2D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet2D"):
    results2D: List


class Result2D(Result, speckle_type=STRUCTURAL_RESULTS + "Result2D"):
    element: Element2D = None
    position: List
    dispX: float = None
    dispY: float = None
    dispZ: float = None
    forceXX: float = None
    forceYY: float = None
    forceXY: float = None
    momentXX: float = None
    momentYY: float = None
    momentXY: float = None
    shearX: float = None
    shearY: float = None
    stressTopXX: float = None
    stressTopYY: float = None
    stressTopZZ: float = None
    stressTopXY: float = None
    stressTopYZ: float = None
    stressTopZX: float = None
    stressMidXX: float = None
    stressMidYY: float = None
    stressMidZZ: float = None
    stressMidXY: float = None
    stressMidYZ: float = None
    stressMidZX: float = None
    stressBotXX: float = None
    stressBotYY: float = None
    stressBotZZ: float = None
    stressBotXY: float = None
    stressBotYZ: float = None
    stressBotZX: float = None


class ResultSet3D(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSet3D"):
    results3D: List


class Result3D(Result, speckle_type=STRUCTURAL_RESULTS + "Result3D"):
    element: Element3D = None
    position: List
    dispX: float = None
    dispY: float = None
    dispZ: float = None
    stressXX: float = None
    stressYY: float = None
    stressZZ: float = None
    stressXY: float = None
    stressYZ: float = None
    stressZX: float = None


class ResultGlobal(Result, speckle_type=STRUCTURAL_RESULTS + "ResultGlobal"):
    model: Model = None
    loadX: float = None
    loadY: float = None
    loadZ: float = None
    loadXX: float = None
    loadYY: float = None
    loadZZ: float = None
    reactionX: float = None
    reactionY: float = None
    reactionZ: float = None
    reactionXX: float = None
    reactionYY: float = None
    reactionZZ: float = None
    mode: float = None
    frequency: float = None
    loadFactor: float = None
    modalStiffness: float = None
    modalGeoStiffness: float = None
    effMassX: float = None
    effMassY: float = None
    effMassZ: float = None
    effMassXX: float = None
    effMassYY: float = None
    effMassZZ: float = None


class ResultSetNode(Result, speckle_type=STRUCTURAL_RESULTS + "ResultSetNode"):
    resultsNode: List


class ResultNode(Result, speckle_type=STRUCTURAL_RESULTS + " ResultNode"):
    node: Node = None
    dispX: float = None
    dispY: float = None
    dispZ: float = None
    rotXX: float = None
    rotYY: float = None
    rotZZ: float = None
    reactionX: float = None
    reactionY: float = None
    reactionZ: float = None
    reactionXX: float = None
    reactionYY: float = None
    reactionZZ: float = None
    constraintX: float = None
    constraintY: float = None
    constraintZ: float = None
    constraintXX: float = None
    constraintYY: float = None
    constraintZZ: float = None
    velX: float = None
    velY: float = None
    velZ: float = None
    velXX: float = None
    velYY: float = None
    velZZ: float = None
    accX: float = None
    accY: float = None
    accZ: float = None
    accXX: float = None
    accYY: float = None
    accZZ: float = None


class ResultSetAll(Base, speckle_type=None):
    resultSet1D: ResultSet1D = None
    resultSet2D: ResultSet2D = None
    resultSet3D: ResultSet3D = None
    resultsGlobal: ResultGlobal = None
    resultsNode: ResultSetNode = None
