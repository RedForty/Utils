# Select the blendshape node, the original mesh, and then target mesh in that order
# Imports ------------------- # 
from collections import OrderedDict

# Methods ------------------- # 
def getOrig(mesh):
    targetMeshShapes = cmds.listRelatives(mesh, shapes=True)
    for shape in targetMeshShapes:
        if 'Orig' in shape:
            return shape



# Start here ---------------- # 
sel = cmds.ls(sl=1)
# blendShapeNode = sel[0]
originMesh     = sel[-2]
targetMesh     = sel[-1]

blendshapes = [x for x in sel if cmds.nodeType(x) == 'blendShape']

blendTargets = OrderedDict()
connections = OrderedDict()

for blendshape in blendshapes:
    blendTargets[blendshape] = cmds.listAttr(blendshape + '.w', multi=True)

# Get the source
# cmds.listConnections(blendShapeNode + '.' + blendTargets[0], d=False, s=True)

# Get the sources
for blendNode, blendTarget in blendTargets.items():
    for i in xrange(len(blendTarget)):
        connections[blendNode + '.' + blendTarget[i]] = cmds.connectionInfo(blendNode + '.' + blendTarget[i], sourceFromDestination=True)

# Break all connections
for destination, source in connections.items():
    if connections[destination]:
        cmds.disconnectAttr(source, destination)

# Set all connected blendshapes to 0
blendShapeValues = {}
for destination, source in connections.items():
    if connections[destination]:
        blendShapeValues[destination] = cmds.getAttr(destination)
        cmds.setAttr(destination, 0)
        sourceShape = cmds.listRelatives(originMesh, shapes=True)[0]
        # After turning off all the blendshapes, it 'adjusts' the mesh. 
        # TransferAttributes to move all the verts into this new position
        # before re-constructing blendshapes
targetOrig = getOrig(targetMesh)
cmds.setAttr(targetOrig + '.intermediateObject', 0)
cmds.transferAttributes(sourceShape, targetOrig, sampleSpace=5, transferPositions=1 )
cmds.delete(targetOrig, ch=True)
cmds.setAttr(targetOrig + '.intermediateObject', 1)
        

# Steal all the blendshapes from the original mesh
blendNode = cmds.blendShape(targetMesh)
index = 0
for destination, source in connections.items():
    if connections[destination]:
        index += 1
        cmds.setAttr(destination, 1)
        sculpt = cmds.duplicate(originMesh, name=destination.rpartition('.')[-1])
        cmds.blendShape(blendNode[0], e=True, target=(targetMesh, index, sculpt[0], 1))
        cmds.connectAttr(destination, blendNode[0] + '.' + sculpt[0])
        # cmds.setAttr(blendNode[0] + '.' + sculpt[0], 1)
        cmds.delete(sculpt)
        cmds.setAttr(destination, 0)
        
# Restore all the connections
for destination, source in connections.items():
    if connections[destination]:
        cmds.connectAttr(source, destination)



