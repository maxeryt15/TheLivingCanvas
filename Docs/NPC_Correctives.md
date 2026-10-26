# Corrective shape keys de NPCs (piloto: Gardener)

Fecha: 2026-10-26. Estado: piloto en la copia de trabajo `ArtSource/NPC/NPCs_Shell_Face_CORRECTIVES_WORK.blend`. Los demás NPCs, el armature, los pesos y las animaciones no se han tocado. El original `NPCs_Shell_Face.blend` queda intacto.

## Herramientas (`Tools/npc_pipeline/`)

- `pose_lib.py`: batería de poses (ArmsUp, ArmsForward, ArmsBack, ElbowBend, ShoulderCross, ShoulderUpElbow, LegKick, LegAbduct, KneeBend, Crouch, Sit, BendForward, Twist_A/B, HeadDown). El eje local y el signo de cada rotación se calibran solos, sin adivinar ejes del rig.
- `corrective_battery.py`: mide las 11 NPCs en todas las poses (A = piel fuera de la prenda, B = prenda dentro de la piel). Salida en `ArtSource/NPC/_Reports/corrective_battery.json`.
- `make_corrective.py`: crea UNA shape key relativa a Basis y su driver. `verify_corrective.py`: valida Idle exacto, intermedias y efectos secundarios. `render_pose_shot.py`: render de una pose con o sin correctivas (`nokey`).

## Método de la shape key

1. Pose problemática → vértices de prenda que cruzan la piel o dejan salir piel → desplazamiento mínimo con holgura de 3 mm.
2. Se extiende 3 anillos con caída 0.6 (corrección localizada).
3. El desplazamiento se pasa a espacio de reposo con la inversa de la matriz de skinning por vértice (las shape keys se aplican antes del skinning).
4. Tres pasadas de refinado, tope de 40 mm por vértice.
5. Multinivel: una key por nivel de la pose (20, 40, 60, 80 y 100 % del ángulo). Una sola key no sirve en ángulos intermedios porque el clipping cambia de forma con el ángulo. Cada key tiene un driver triangular (TRANSFORMS, rotación local de un hueso) que vale 1 en su nivel y 0 en los vecinos; la última se mantiene en 1 más allá. Los pesos de las keys vecinas suman 1.

Piloto Gardener, `ShoulderCross_R` (peor caso en mm; A = piel que asoma, B2 = prenda más hundida que en reposo):

| Fracción de la pose | Sin keys (A / B2) | Con keys (A / B2) |
|---|---|---|
| 0.3 | 12.6 / 5.8 | 3.6 / 4.1 |
| 0.5 | 14.3 / 24.9 | 8.4 / 7.8 |
| 0.7 | 19.3 / 31.2 | 3.8 / 10.3 |
| 1.0 | 16.2 / 33.6 | 0.3 / 12.6 |

Residual: 12.6 mm al 100 % (tope de 60 mm de desplazamiento por vértice) y entre niveles (mezcla lineal). Idle idéntico (0.0 mm) y sin cambios en las otras 24 poses.

### Picos del borde de manga (ArmsUp)

Los dientes del borde de la manga con los brazos arriba eran aristas de la prenda estiradas hasta 12 veces su largo en reposo (vértices del aro de la sisa con pesos mezclados entre `spine_03` y `upperarm`). `make_corrective.py ... relax` añade una relajación de aristas (PBD, 40 iteraciones) en las primeras 3 de 6 pasadas y deja las últimas 3 solo con holgura de piel. Resultado en Gardener, ArmsUp al 100 %: aristas estiradas (más de 1.8 veces) 74 → 24 (R) y 82 → 24 (L); estiramiento máximo 12.3 → 3.6 (R) y 9.0 → 3.6 (L). Coste: la piel que asoma (A) sube en R de 3.2 a 17.0 mm al 100 % y aparecen 8-9 mm al 80-90 %, porque la tela se recoge en vez de estirarse.

## Extension a Tourist, Cafe, Curator y Painter (2026-10-26)

Generadas con `batch_correctives.py` (en paralelo, relajacion de aristas activa) y unidas a la copia de trabajo con `merge_correctives.py`. JSON en `ArtSource/NPC/_Reports/correctives/`. Total: Tou 45 keys, Caf 30, Cur 40, Pnt 20 (+20 de Gar). Idle exacto (0.0 mm) en los 5 NPCs. Maximos (A piel que asoma / B2 prenda hundida, mm) sin keys -> con keys:

| NPC | Familias | Resultado |
|---|---|---|
| Tou | Hips_Sit, L/R_Shoulder_Cross, L_Shoulder_Up, L/R_Knee_Bend, L/R_Leg_Abduct, Spine_Bend | ShoulderCross_L 28.6/17.8 -> 0.3/0.4; ArmsUp_L 19.0/12.0 -> 1.4/5.9; LegKick_L 28.6/30.8 -> 8.3/9.3; BendForward 28.5/14.5 -> 2.9/12.5; LegAbduct 0/16 -> 0/2 |
| Caf | L/R_Shoulder_Up, R_Shoulder_Forward, L/R_Knee_Bend, L_Leg_Abduct | ArmsUp_R 1.7/22.0 -> 0/5.3; LegAbduct_L B2 22.0 -> 4.7; KneeBend 22.0 -> 4.7-7.4 |
| Cur | Hips_Crouch, L_Knee_Bend, L/R_Shoulder_Cross, R_Leg_Abduct, Spine_Bend/Twist | A baja (BendForward 32.7 -> 10.4, Crouch 32.7 -> 17.9); B2 sigue ~30 mm: es un pico constante de un vertice (falso positivo de la metrica), sin cambio posible |
| Pnt | L/R_Elbow_Bend, R_Shoulder_Up, Neck_Down | ElbowBend_L 18.0/30.5 -> 0.5/17.1; ArmsUp_R B2 21.4 -> 2.4; HeadDown 25.2/15.5 -> 0/12.2 |

Empeoran (poses combinadas, las keys de familias distintas se suman):
- Tou Crouch (B2 25.4 -> 34.1; A 32.6 -> 15.5) y Tou Sit (A 5.4 -> 12.4; B2 34.0 -> 30.2). Render de Tou Sit con/sin keys: sin diferencia visible.
- Caf Sit (A 0 -> 8.0, B2 12.7 -> 1.1), Cur Sit (B2 17.7 -> 27.6), Pnt ShoulderUpElbow_R (A 1.3 -> 5.5).
- Causa: las keys se calibraron en poses de una sola articulacion; al combinar rodilla+cadera o hombro+codo se mezclan dos correctivas. Mitigacion posible si molesta en juego: quitar la familia `*_Knee_Bend` en Tou (mejora Sit a B2 ~20, empeora KneeBend suelto).

Sin verificar con renders: solo se miro Tou Sit. Faltan Cou, Doc, Gen, Grd, Rose, Stu (no se han medido para decidir si tienen clipping real). Nada de esto llega a Unity todavia (drivers no se exportan y `export_shell11.py` lee `NPCs_Shell_Test.blend`).

### Resto de NPCs (2026-10-26)

Medidos los 6 restantes (sin keys). Grd y Stu: sin clipping real (solo `head` constante, falso positivo) -> sin correctivas. Doc y Gen: las pruebas empeoraron poses y se descartaron. Cou: `L_Shoulder_Up` empeoraba B2 (15.6 -> 36) y se quito.

| NPC | Keys | Resultado |
|---|---|---|
| Cou | R_Shoulder_Up (5) | sin empeoramientos; L descartada |
| Rose | L/R_Shoulder_Up, L/R_Elbow_Bend (20) | ElbowBend B2 22.3 -> 0.6/1.1; ArmsUp B2 19.7 -> 8.1/8.8; ShoulderUpElbow_L A 0 -> 8.8, B2 24.0 -> 19.6 |
| Doc, Gen | ninguna | L_Elbow_Bend (Doc) y *_Arm_Elbow (Gen) mejoraban una pose y empeoraban otra |
| Grd, Stu | ninguna | sin clipping real |

Backup previo: `NPCs_Shell_Face_CORRECTIVES_WORK_BACKUP_before_ext2.blend`.

## Limitación con Unity (importante)

El FBX exporta las shape keys como blend shapes, pero NO exporta los drivers. En Unity las blend shapes quedan con peso 0 y hay que activarlas por script, leyendo la rotación del mismo hueso. Equivalente en Unity (Humanoid):

```csharp
// Añadir al NPC. Cinco blend shapes triangulares por rotación del hueso (0-100).
public class NpcCorrective : MonoBehaviour
{
    public SkinnedMeshRenderer mesh;
    public Animator animator;
    public HumanBodyBones bone = HumanBodyBones.RightUpperArm;
    public string[] blendShapes = { "Corrective_R_Shoulder_Cross_20", "Corrective_R_Shoulder_Cross_40", "Corrective_R_Shoulder_Cross_60", "Corrective_R_Shoulder_Cross_80", "Corrective_R_Shoulder_Cross_100" };
    public float[] levels = { 0.2f, 0.4f, 0.6f, 0.8f, 1f };
    public Vector3 axis = Vector3.forward;   // eje local de Blender equivalente en Unity (comprobar al importar)
    public float sign = 1f, fullDeg = 100f;
    int[] idx; Transform t;
    void Start() { t = animator.GetBoneTransform(bone); idx = System.Array.ConvertAll(blendShapes, mesh.sharedMesh.GetBlendShapeIndex); }
    void LateUpdate()
    {
        t.localRotation.ToAngleAxis(out float ang, out Vector3 ax);
        if (ang > 180f) ang -= 360f;
        float ph = sign * ang * Vector3.Dot(ax, axis) / fullDeg;
        for (int i = 0; i < idx.Length; i++)
        {
            float lo = i > 0 ? levels[i - 1] : Mathf.Max(0f, levels[0] - (levels[1] - levels[0]));
            float hi = i + 1 < levels.Length ? levels[i + 1] : levels[i];
            float w = Mathf.Clamp01((ph - lo) / (levels[i] - lo));
            if (i + 1 < levels.Length) w = Mathf.Min(w, Mathf.Clamp01((hi - ph) / (hi - levels[i])));
            mesh.SetBlendShapeWeight(idx[i], 100f * w);
        }
    }
}
```

Hay que comprobar el eje equivalente (Blender es Z-up y el FBX se exporta con -Z/Y). No está probado en Unity.
