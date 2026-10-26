using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.InputSystem;
using UnityEngine.Playables;

// Dev only (solo Editor): en Play reproduce, en bucle, todas las animaciones humanoides del proyecto en todos los NPCs de la escena NpcLineup.
// Flechas der/izq = siguiente/anterior, Espacio = pausa/continuar (auto-avance), Tab = alterna auto-avance.
// Se excluyen: poses estaticas (<0.1 s), T-Pose, clips _probe y las poses por NPC (Pose_<NPC>_*; las 5 Stand_* genericas si entran).
public class NpcLineupAnimCycler : MonoBehaviour
{
    public float minSeconds = 3f;
    public float maxSeconds = 8f;

#if UNITY_EDITOR
    class Slot { public Animator a; public PlayableGraph g; public AnimationClipPlayable p; }
    readonly List<AnimationClip> clips = new List<AnimationClip>();
    readonly List<string> sources = new List<string>();
    readonly List<Slot> slots = new List<Slot>();
    int index = -1; float t; float dur; bool auto = true;

    void Start()
    {
        foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:AnimationClip", new[] { "Assets/_TheLivingCanvas/Art/Animations" }))
        {
            var path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid);
            foreach (var o in UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path))
            {
                var c = o as AnimationClip;
                if (c == null || c.name.StartsWith("__preview") || !c.isHumanMotion || c.length < 0.1f) continue;
                if (c.name.Contains("TPose") || c.name.Contains("T-Pose") || c.name.StartsWith("_probe") || c.name.StartsWith("Pose_")) continue;
                clips.Add(c); sources.Add(System.IO.Path.GetFileName(System.IO.Path.GetDirectoryName(path)));
            }
        }
        foreach (var a in GetComponentsInChildren<Animator>())
        {
            a.applyRootMotion = false;
            var s = new Slot { a = a, g = PlayableGraph.Create("cycler_" + a.name) };
            s.g.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
            var output = AnimationPlayableOutput.Create(s.g, "out", a);
            s.p = AnimationClipPlayable.Create(s.g, clips[0]); output.SetSourcePlayable(s.p);
            s.g.Play(); slots.Add(s);
        }
        Debug.Log($"[NpcLineupAnimCycler] {clips.Count} clips x {slots.Count} NPCs");
        Next(1);
    }

    void Next(int dir)
    {
        if (clips.Count == 0) return;
        index = (index + dir + clips.Count) % clips.Count;
        var c = clips[index];
        foreach (var s in slots)
        {
            s.p.Destroy();
            s.p = AnimationClipPlayable.Create(s.g, c); s.p.SetApplyFootIK(true);
            s.g.GetOutput(0).SetSourcePlayable(s.p);
        }
        t = 0f; dur = c.isLooping ? Mathf.Clamp(c.length * Mathf.Ceil(minSeconds / c.length), minSeconds, maxSeconds) : Mathf.Clamp(c.length + 0.7f, minSeconds * 0.5f, maxSeconds);
        Debug.Log($"[NpcLineupAnimCycler] {index + 1}/{clips.Count} {sources[index]} | {c.name} ({c.length:0.00}s, loop={c.isLooping})");
    }

    void Update()
    {
        var kb = Keyboard.current;
        if (kb != null)
        {
            if (kb.rightArrowKey.wasPressedThisFrame) Next(1);
            if (kb.leftArrowKey.wasPressedThisFrame) Next(-1);
            if (kb.tabKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame) auto = !auto;
        }
        if (clips.Count == 0) return;
        t += Time.deltaTime;
        if (auto && t >= dur) Next(1);
        else if (!clips[index].isLooping && t > clips[index].length)   // un clip de una sola pasada: repetirlo hasta que toque avanzar
            foreach (var s in slots) s.p.SetTime(0);
    }

    void OnGUI()
    {
        if (clips.Count == 0) return;
        var style = new GUIStyle(GUI.skin.label) { fontSize = 20 }; style.normal.textColor = Color.white;
        GUI.Label(new Rect(14, 10, 1000, 30), $"{index + 1}/{clips.Count}  [{sources[index]}] {clips[index].name}  {(auto ? "AUTO" : "PAUSA")}   (flechas = anterior/siguiente, Espacio = pausa)", style);
    }

    void OnDestroy() { foreach (var s in slots) if (s.g.IsValid()) s.g.Destroy(); }
#endif
}
