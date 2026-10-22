# NPC face rig (Blender -> Unity)

Fuente de trabajo: `ArtSource/NPC/NPCs_Shell_Face.blend` (copia de `NPCs_Shell_Test.blend`, que NO se ha tocado con el rig facial).
Scripts: `Tools/npc_pipeline/face_rig.py` (construye), `export_face_diag.py` (exporta a `ArtSource/_Exports/FaceDiag/`, sin tocar `Assets/`).
Estado: Blender validado, FBX validado (reimportado en Blender). Unity import: PENDIENTE. Unity runtime: PENDIENTE.
FBX de diagnostico: `ArtSource/_Exports/FaceDiag/{Cafe,Courier,Curator,Docent,Gardener,Gentleman,Guard,Painter,Rose_Receptionist,Student,Tourist}.fbx`.
Backups: `ArtSource/NPC/NPCs_Shell_Face_BACKUP_before_audit.blend`, `..._BACKUP_before_signoff.blend` (antes de subir sonrisa/ceno y refinar mouth_open). `export_shell11.py` sigue leyendo `NPCs_Shell_Test.blend` (no se ha cambiado).

## Arquitectura (hibrida)
- **Ojos**: huesos `eye_L` / `eye_R` (hijos de `head`, deform). Cada globo ocular (cupula con blanco/iris/pupila) esta pesado 100% a su hueso. +2 huesos sobre los 53 del cuerpo. En Unity mapealos como LeftEye / RightEye (Humanoid, opcional).
- **Mirada**: en Blender el hueso NO deform `eye_aim` + restricciones Damped Track (influencia 0 por defecto) + Limit Rotation (+-20 deg horizontal, +-12 deg vertical; a +-25 el iris llegaba a la comisura). Las restricciones y `eye_aim` NO se exportan (`use_armature_deform_only=True`, el FBX no lleva restricciones). Equivalente en Unity: `Animator.SetLookAtPosition` + `SetLookAtWeight(w, body, head, eyes)` en `OnAnimatorIK`, con los ojos mapeados en el Avatar; o rotar `eye_L/eye_R` por script limitando a +-20 deg (yaw, eje Z local del hueso) y +-12 deg (pitch, eje X local). Los controles que debe mover Unity: los 9 blend shapes y los dos huesos de ojo; `eye_aim` y las restricciones solo existen en Blender.
- **Parpados / boca / cejas**: shape keys = blend shapes de Unity en el SkinnedMeshRenderer del NPC:
  `blink, mouth_open, mouth_smile, mouth_frown, mouth_round, mouth_wide, brow_raise, brow_lower, brow_worry` (0..1).
- **Interior de la boca**: un quad oscuro (`NPC_MouthInside`) detras de los labios en reposo, pesado a `head`; la key `mouth_open` lo adelanta para formar la ranura.

## Expresiones (combinaciones, valores 0..1)
| Expresion | Blend shapes |
|---|---|
| Neutral | todo a 0 |
| Sonrisa suave | mouth_smile 0.6 |
| Triste / preocupado | mouth_frown 0.6, brow_worry 1.0 |
| Sorpresa | mouth_open 0.8, mouth_round 0.4, brow_raise 1.0 |
| Hablando | mouth_open 0.2-0.8 oscilando, mouth_wide / mouth_round segun vocal |
| Parpadeo | blink 0 -> 1 -> 0 en ~0.15 s |

## Limitaciones conocidas
- Los labios son una malla gruesa y cerrada (sin cavidad ni dientes). `mouth_open` v2: el labio inferior baja ~1.2 cm y la tarjeta oscura `NPC_MouthInside` pasa, solo en esa key, por delante del labio para formar una ranura oscura plana. Se lee como boca abierta estilizada; de perfil la ranura queda ligeramente flotante delante de los labios. En reposo la tarjeta (22 x 8 mm) queda detras de los labios.
- Sin parpados modelados: `blink` comprime la piel alrededor del ojo y aplasta el globo; queda una rendija fina.
- `blink` y las cejas se tocaron solo por geometria; en Cou, Cur, Pnt, Stu hay gafas/accesorios que no se mueven con la cara.
- La malla debe estar triangulada antes de crear los shape keys (el exportador triangula ngons con bmesh y perderia los shape keys). Rose se triangulo por eso.
- Sign-off visual: `mouth_smile` subido x1.8 (~9 mm) y `mouth_frown` x1.8 (~7 mm) porque a 5/4 mm no se distinguian de cerca en Gar/Caf; `face_rig.py` ya lleva las nuevas amplitudes. `mouth_wide` (3.8 mm) sigue siendo muy sutil.
- `mouth_open` v2.1: el borde inferior de la ranura sigue al labio inferior (y_front+3 mm) para que de perfil no flote; sigue siendo una ranura rectangular plana.
- Gaze: en el sign-off se vio bien a +-20 deg / +-12 deg en Gar y Rose (el iris no sale de la cuenca). Blink se lee como linea de parpado cerrado (Gar, Caf, Rose), aceptable.

## Checklist manual en Unity
1. Importar `FaceDiag/<NPC>.fbx` con Rig = Humanoid, comprobar en Configure Avatar que el cuerpo mapea igual que antes; opcional LeftEye/RightEye = eye_L/eye_R.
2. Comprobar que el SkinnedMeshRenderer lista los 9 blend shapes y que los materiales/texturas siguen (el material `NPC_MouthInside` es nuevo, plano oscuro).
3. Reproducir una animacion Mixamo existente (Idle, Walking) y confirmar que cuerpo y ropa se comportan como antes (Gen, Grd incluidos).
4. Mover cada blend shape 0 -> 1 -> 0 y comprobar que vuelve a neutro.
5. Rotar eye_L/eye_R +-20 deg horizontal y +-12 deg vertical: sin que el globo asome fuera de la cuenca.
6. Probar OnAnimatorIK / SetLookAtPosition.

## Piloto Unity (Gen) — 2026-10-22
Piloto aislado en `Assets/_Dev/NPCFacePilot/` (`Gen/Gen_Face.fbx`, `GenFacePilot.unity`, `Shots/`). Producción intacta.
- BUG corregido en `face_rig.py`: borrar `Basis` primero en las shape keys horneaba la siguiente key en la malla base (deriva acumulada, cejas x4 de alto). Ahora se borran en orden inverso. `NPCs_Shell_Face.blend` se regeneró desde `NPCs_Shell_Test.blend` (backup del contaminado: `NPCs_Shell_Face_BACKUP_contaminated_basis.blend`).
- Unity: Avatar Humanoid valido, 55 huesos, 9 blend shapes, 28 materiales. Importar con `useFileScale=true`, escala 1, y Blend Shape Normals = None (con "Calculate" las normales de los shapes salian rotas: manchas oscuras en la mejilla).
- Mirada: `eye_L/eye_R` funcionan. Eje local Z = giro horizontal, eje local X = vertical (Y = roll). 20 deg => iris ~5.5 mm.
- Los clips Mixamo no llevan curvas de blend shape ni de ojos: el Animator no los pisa.
