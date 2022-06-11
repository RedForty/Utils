# Maya Timeline Utilities

from maya import cmds, mel

TIMELINE = mel.eval('string $tmpString=$gPlayBackSlider')

def get_timeline_selection():
    if cmds.timeControl(TIMELINE, q=True, rangeVisible=True):
        return cmds.timeControl(TIMELINE, q=True, rangeArray=True)
    else: 
        return []

def get_timeline_range():
    start_frame = cmds.playbackOptions(q=True, minTime=True)
    end_frame = cmds.playbackOptions(q=True, maxTime=True)
    return [start_frame, end_frame]

def get_work_time(node=None):
    
    keyframes = []
    
    timeline_selection = get_timeline_selection() # Selection takes priority
    if timeline_selection:
        timeline_selection = [x * 1.0 for x in range(int(min(timeline_selection)), int(max(timeline_selection))+1)]
    
    if node:
        keyframes = cmds.keyframe(node, q=True) or []
        keyframes = list(set(keyframes)) # All the keys

    time_range = get_timeline_range()
    start      = min(time_range + keyframes)
    end        = max(time_range + keyframes)
    keyframes = [x * 1.0 for x in range(int(start), int(end)+1)]
        
    if timeline_selection:
        new_keyframes = []
        for key in keyframes:
            if key in timeline_selection:
                new_keyframes.append(key)
        keyframes = new_keyframes # Crop to selection    
    
    return keyframes
