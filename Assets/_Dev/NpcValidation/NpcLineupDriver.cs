using UnityEngine;
using UnityEngine.InputSystem;

// Dev only: fuerza el ciclo de caminar en sitio de todos los NPCs de la escena NpcLineup.
// Tecla C: alterna _Cull de los materiales (instancias en memoria, no toca los assets) entre 2 (culling normal) y 0 (doble cara).
public class NpcLineupDriver : MonoBehaviour
{
    public float speed = 1f;
    Material[] mats;
    bool twoSided = true;   // los materiales de ropa ya vienen con _Cull=0; la tecla C los pasa a culling normal (2) para comparar

    void Start()
    {
        var list = new System.Collections.Generic.List<Material>();
        foreach (var a in GetComponentsInChildren<Animator>())
        {
            a.applyRootMotion = false;
            a.SetFloat("Speed", speed);
            if (a.runtimeAnimatorController == null || a.avatar == null || !a.avatar.isValid)
                Debug.LogError($"[NpcLineup] {a.name}: controller o avatar invalido");
        }
        foreach (var s in GetComponentsInChildren<SkinnedMeshRenderer>())
        {
            if (s.sharedMesh == null) Debug.LogError($"[NpcLineup] {s.name}: sin malla");
            foreach (var m in s.materials) if (m != null && m.HasProperty("_Cull")) list.Add(m);   // .materials = instancias
        }
        mats = list.ToArray();
        Debug.Log($"[NpcLineup] {mats.Length} materiales con _Cull. Tecla C: culling normal <-> doble cara");
    }

    void Update()
    {
        var kb = Keyboard.current;
        if (kb != null && kb.cKey.wasPressedThisFrame)
        {
            twoSided = !twoSided;
            foreach (var m in mats) m.SetFloat("_Cull", twoSided ? 0f : 2f);
            Debug.Log("[NpcLineup] doble cara: " + twoSided);
        }
    }
}
