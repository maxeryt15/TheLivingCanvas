using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Busqueda ampliada (en segundo plano, un intento por tick del editor) de separacion de brazo/codo/hombro para las poses de pie
    /// que aun tienen vertices de ropa atravesando el cuerpo. Solo reemplaza un Pose_&lt;Npc&gt;_&lt;Pose&gt; si el resultado mejora.
    /// Resultado en Temp/pose_search.txt.
    /// </summary>
    public static class NpcPoseSearch
    {
        const string Dir = "Assets/_TheLivingCanvas/Art/Animations/Poses/";
        static readonly Dictionary<string, Dictionary<string, float>> Deltas = new Dictionary<string, Dictionary<string, float>>
        {
            { "Stand_HandsOnHips", new Dictionary<string, float> { { "Head Nod Down-Up", 0.05f } } },
            { "Stand_HandsBehind", new Dictionary<string, float> { { "Head Nod Down-Up", -0.05f } } },
            { "Stand_OneHipRight", new Dictionary<string, float> { { "Spine Left-Right", 0.06f }, { "Head Tilt Left-Right", -0.08f }, { "Left Lower Leg Stretch", -0.12f } } },
            { "Stand_OneHipLeft", new Dictionary<string, float> { { "Spine Left-Right", -0.06f }, { "Head Tilt Left-Right", 0.08f }, { "Right Lower Leg Stretch", -0.12f } } },
            { "Stand_Relaxed", new Dictionary<string, float> { { "Head Tilt Left-Right", 0.03f } } },
        };

        class Job { public string npc, pose; }
        static List<Job> jobs; static int ji; static GameObject rig; static List<float[]> grid; static int gi;
        static int bestScore; static float[] best; static StringBuilder log; static AnimationClip lastClip;

        public static void Start(string[] npcs, string[] poses)
        {
            jobs = new List<Job>(); foreach (var n in npcs) foreach (var p in poses) jobs.Add(new Job { npc = n, pose = p });
            grid = new List<float[]>();
            foreach (var a in new[] { 0.1f, 0.2f, 0.3f, 0.4f, 0.5f, 0.65f, 0.8f })
                foreach (var e in new[] { 0f, 0.15f, 0.3f, 0.45f, 0.6f, 0.8f })
                    foreach (var s in new[] { 0f, 0.15f, 0.3f })
                        grid.Add(new[] { a, e, s });
            ji = 0; gi = 0; rig = null; log = new StringBuilder(); bestScore = int.MaxValue;
            EditorApplication.update += Tick;
        }

        static int Total(string res) { int i = res.IndexOf("total="); return int.Parse(new string(res.Substring(i + 6).TakeWhile(char.IsDigit).ToArray())); }

        static void Tick()
        {
            try
            {
                if (ji >= jobs.Count) { Finish(); return; }
                var job = jobs[ji];
                if (rig == null)
                {
                    var pf = job.npc == "Rose" ? AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_TheLivingCanvas/Art/Models/NPC/Rose/Rose_Receptionist.fbx") : AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/_TheLivingCanvas/Prefabs/NPC/NPC_{job.npc}.prefab");
                    rig = (GameObject)PrefabUtility.InstantiatePrefab(pf); rig.transform.position = new Vector3(0, -500, 0);
                    gi = 0; bestScore = int.MaxValue; best = null;
                    var cur = AssetDatabase.LoadAssetAtPath<AnimationClip>(Dir + $"Pose_{job.npc}_{job.pose}.anim");
                    bestScore = Total(NpcClipAudit.Test(job.npc, cur, 1));   // el resultado actual es la marca a batir
                    log.AppendLine($"{job.npc} {job.pose}: actual={bestScore}");
                    if (bestScore == 0) { Object.DestroyImmediate(rig); rig = null; ji++; return; }
                }
                if (gi >= grid.Count)
                {
                    if (best != null)
                    {
                        var s = Add(job, best);   // reconstruye el mejor y lo guarda en el clip definitivo
                        var src = AssetDatabase.LoadAssetAtPath<AnimationClip>(Dir + "_probe.anim");
                        AssetDatabase.DeleteAsset(Dir + $"Pose_{job.npc}_{job.pose}.anim");
                        AssetDatabase.CopyAsset(Dir + "_probe.anim", Dir + $"Pose_{job.npc}_{job.pose}.anim");
                        log.AppendLine($"   -> mejora a {bestScore} con a={best[0]} e={best[1]} s={best[2]}");
                    }
                    else log.AppendLine("   -> sin mejora");
                    Object.DestroyImmediate(rig); rig = null; ji++; return;
                }
                var g = grid[gi++];
                Add(job, g);
                var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(Dir + "_probe.anim");
                int sc = Total(NpcClipAudit.Test(job.npc, clip, 1));
                if (sc < bestScore) { bestScore = sc; best = g; }
            }
            catch (System.Exception ex) { log.AppendLine("ERROR " + ex); Finish(); }
        }

        static string Add(Job job, float[] g)
        {
            var delta = new Dictionary<string, float>(Deltas["Stand_" + job.pose]);
            delta["Left Shoulder Down-Up"] = g[2]; delta["Right Shoulder Down-Up"] = g[2];
            NpcPoseBuilder.BuildStand("_probe", rig, NpcPoseBuilder.Poses["Stand_" + job.pose], delta, g[0], g[1]);
            return "";
        }

        static void Finish()
        {
            EditorApplication.update -= Tick;
            if (rig != null) Object.DestroyImmediate(rig);
            AssetDatabase.SaveAssets(); AssetDatabase.Refresh();
            System.IO.File.WriteAllText("Temp/pose_search.txt", log.ToString() + "\nDONE");
        }
    }
}
