#!/bin/bash
# Reconstruye ArtSource/NPC/NPCs_Shell_Test.blend con la cascara robusta a las animaciones (etapas A, B en paralelo, C).
BL="/d/SteamLibrary/steamapps/common/Blender/blender.exe"
NPC="/d/TheLivingCanvas/ArtSource/NPC"
TP="/d/TheLivingCanvas/Tools/npc_pipeline"
mkdir -p "$NPC/_shell_tmp" && rm -f "$NPC"/_shell_tmp/*.json
if [ "$1" != "skipA" ]; then "$BL" -b "$NPC/All10_Review_VanGogh_BACKUP_before_lips.blend" --python "$TP/shell_stageA.py" 2>&1 | grep -E "^STAGEA|Error|Traceback"; fi
for p in Caf Cur Grd Stu Gar Tou Gen Cou Doc Pnt Rose; do
  "$BL" -b "$NPC/NPCs_Shell_Pre.blend" --python "$TP/shell_stageB.py" -- $p 2>&1 | grep -E "^BDONE|^B .*poses usadas|Error|Traceback" &
done
wait
"$BL" -b "$NPC/NPCs_Shell_Pre.blend" --python "$TP/shell_stageC.py" 2>&1 | grep -E "^CASCARA|^STAGEC|Error|Traceback"
echo FIN
