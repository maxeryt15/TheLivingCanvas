using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Vuelca las animaciones de un NPC (caminar + poses de pie) a JSON para probarlas en Blender: por fotograma, posicion y rotacion de cada hueso
    /// relativas a la raiz del NPC. Blender las aplica con Tools/npc_pipeline/apply_unity_anims.py.
    /// Salida: ArtSource/NPC/Anims/&lt;Npc&gt;.json
    /// </summary>
    public static class NpcAnimExport
    {
        const string OutDir = "ArtSource/NPC/Anims";
        static readonly string[] Poses = { "HandsOnHips", "HandsBehind", "OneHipRight", "OneHipLeft", "Relaxed" };
        static readonly string[] Men = { "Guard", "Gardener", "Gentleman", "Docent" };

        static string F(float v) => v.ToString("0.#####", CultureInfo.InvariantCulture);

        public static string Export(string npc)
        {
            var pf = npc == "Rose" ? AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_TheLivingCanvas/Art/Models/NPC/Rose/Rose_Receptionist.fbx") : AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/_TheLivingCanvas/Prefabs/NPC/NPC_{npc}.prefab");
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(pf);
            inst.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            var an = inst.GetComponent<Animator>(); an.enabled = false;
            var root = inst.transform;

            var set = new HashSet<Transform>();
            foreach (var r in inst.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                foreach (var b in r.bones) for (var t = b; t != null && t != root; t = t.parent) set.Add(t);
            var bones = set.OrderBy(t => Depth(t, root)).ToList();

            var sb = new StringBuilder();
            sb.Append("{\"npc\":\"" + npc + "\",\"bones\":[" + string.Join(",", bones.Select(b => "\"" + b.name + "\"")) + "],\"rest\":");
            sb.Append(Frame(bones, root));
            sb.Append(",\"clips\":{");

            var clips = new List<AnimationClip>();
            var walk = AssetDatabase.LoadAssetAtPath<AnimationClip>($"Assets/_TheLivingCanvas/Art/Animations/Gait/{(Men.Contains(npc) ? "Walk_Male" : "Walk_Female")}.anim");
            clips.Add(walk);
            foreach (var p in Poses) clips.Add(AssetDatabase.LoadAssetAtPath<AnimationClip>($"Assets/_TheLivingCanvas/Art/Animations/Poses/Pose_{npc}_{p}.anim"));

            bool first = true;
            foreach (var clip in clips)
            {
                if (clip == null) continue;
                bool isWalk = clip == walk;
                float fps = isWalk ? 30f : 10f;
                int n = Mathf.Max(2, Mathf.RoundToInt(clip.length * fps));
                if (!first) sb.Append(",");
                first = false;
                sb.Append("\"" + clip.name + "\":{\"fps\":" + F(fps) + ",\"loop\":true,\"frames\":[");
                for (int i = 0; i < n; i++)
                {
                    clip.SampleAnimation(inst, clip.length * i / n);
                    if (i > 0) sb.Append(",");
                    sb.Append(Frame(bones, root));
                }
                sb.Append("]}");
            }
            sb.Append("}}");
            Object.DestroyImmediate(inst);
            Directory.CreateDirectory(OutDir);
            string path = $"{OutDir}/{npc}.json";
            File.WriteAllText(path, sb.ToString());
            return $"{npc}: {bones.Count} huesos, {clips.Count(c => c != null)} clips, {new FileInfo(path).Length / 1024} KB";
        }


        /// <summary>Todas las animaciones de un NPC (caminar, poses, Mixamo, saltos) muestreadas en <paramref name="frames"/> fotogramas cada una, para calcular la
        /// cascara visible en TODAS las poses. Salida: ArtSource/NPC/AnimsAll/&lt;Npc&gt;.json (mismo formato que Export).</summary>
        public static string ExportAll(string npc, int frames)
        {
            var pf = npc == "Rose" ? AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_TheLivingCanvas/Art/Models/NPC/Rose/Rose_Receptionist.fbx") : AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/_TheLivingCanvas/Prefabs/NPC/NPC_{npc}.prefab");
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(pf);
            inst.transform.SetPositionAndRotation(new Vector3(0, -900, 0), Quaternion.identity);
            var an = inst.GetComponent<Animator>(); an.enabled = false;
            var root = inst.transform;
            var set = new HashSet<Transform>();
            foreach (var r in inst.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                foreach (var b in r.bones) for (var t = b; t != null && t != root; t = t.parent) set.Add(t);
            var bones = set.OrderBy(t => Depth(t, root)).ToList();
            var sb = new StringBuilder();
            sb.Append("{\"npc\":\"" + npc + "\",\"bones\":[" + string.Join(",", bones.Select(b => "\"" + b.name + "\"")) + "],\"rest\":");
            sb.Append(Frame(bones, root));
            sb.Append(",\"clips\":{");
            var clips = new List<AnimationClip>();
            clips.Add(AssetDatabase.LoadAssetAtPath<AnimationClip>($"Assets/_TheLivingCanvas/Art/Animations/Gait/{(Men.Contains(npc) ? "Walk_Male" : "Walk_Female")}.anim"));
            foreach (var p in Poses) clips.Add(AssetDatabase.LoadAssetAtPath<AnimationClip>($"Assets/_TheLivingCanvas/Art/Animations/Poses/Pose_{npc}_{p}.anim"));
            foreach (var path in Directory.GetFiles("Assets/_TheLivingCanvas/Art/Animations/Mixamo", "*.fbx"))
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path.Replace('\\', '/'))) { var c = o as AnimationClip; if (c != null && !c.name.StartsWith("__preview")) clips.Add(c); }
            var wanted = new[] { "Jump_Full_Short", "Jump_Full_Long", "Rig|Jump_Start", "Rig|Jump_Loop", "Rig|Jump_Land" };
            foreach (var g in AssetDatabase.FindAssets("t:Model", new[] { "Assets/_TheLivingCanvas/Art/Animations/KayKit", "Assets/_TheLivingCanvas/Art/Animations/UAL" }))
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(AssetDatabase.GUIDToAssetPath(g))) { var c = o as AnimationClip; if (c != null && wanted.Contains(c.name) && !clips.Any(x => x.name == c.name)) clips.Add(c); }
            bool first = true;
            foreach (var clip in clips)
            {
                if (clip == null) continue;
                if (!first) sb.Append(",");
                first = false;
                sb.Append("\"" + clip.name.Replace("|", "_") + "\":{\"fps\":1,\"loop\":true,\"frames\":[");
                for (int i = 0; i < frames; i++)
                {
                    clip.SampleAnimation(inst, clip.length * i / Mathf.Max(1, frames - 1));
                    if (i > 0) sb.Append(",");
                    sb.Append(Frame(bones, root));
                }
                sb.Append("]}");
            }
            sb.Append("}}");
            Object.DestroyImmediate(inst);
            Directory.CreateDirectory("ArtSource/NPC/AnimsAll");
            string outp = $"ArtSource/NPC/AnimsAll/{npc}.json";
            File.WriteAllText(outp, sb.ToString());
            return $"{npc}: {clips.Count(c => c != null)} clips x {frames} -> {new FileInfo(outp).Length / 1024} KB";
        }

        static int Depth(Transform t, Transform root) { int d = 0; for (; t != null && t != root; t = t.parent) d++; return d; }

        // [[px,py,pz,qx,qy,qz,qw], ...] en el espacio local de la raiz del NPC
        static string Frame(List<Transform> bones, Transform root)
        {
            var sb = new StringBuilder("[");
            for (int i = 0; i < bones.Count; i++)
            {
                var b = bones[i];
                Vector3 p = root.InverseTransformPoint(b.position);
                Quaternion q = Quaternion.Inverse(root.rotation) * b.rotation;
                if (i > 0) sb.Append(",");
                sb.Append("[" + F(p.x) + "," + F(p.y) + "," + F(p.z) + "," + F(q.x) + "," + F(q.y) + "," + F(q.z) + "," + F(q.w) + "]");
            }
            return sb.Append("]").ToString();
        }
    }
}
