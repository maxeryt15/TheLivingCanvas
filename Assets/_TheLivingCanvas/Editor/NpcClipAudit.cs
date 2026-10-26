using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Mide el clipping de los NPC en movimiento sobre una copia limpia de cada prefab (no toca la escena):
    ///  - POKE: vertices del cuerpo (_Low) que quedan por FUERA de una prenda en la pose, por encima de lo que ya pasa en reposo.
    ///  - FLOAT: vertices de accesorios que se alejan del cuerpo/prenda mas que en reposo (piezas que flotan o se despegan).
    ///  - STRETCH: aristas que se alargan mas de x2.6 respecto al reposo (agujas, tela estirada).
    /// Se evaluan Walk (muestras a lo largo del ciclo), Idle_A/Idle_B/Brazos cruzados.
    /// </summary>
    public static class NpcClipAudit
    {
        static readonly string[] Garments = { "_Suit", "_Pants", "_Tee", "_Shirt", "_Dress", "_Top", "_Shorts", "_Apron" };
        static readonly string[] SkipAcc = { "_Low", "_Hair", "_Eyes", "_Brows", "_Lipstick", "_Freckles", "_LipScar", "_Wart", "_Mole", "_Glasses" };
        static readonly HashSet<string> Men = new HashSet<string> { "Guard", "Gardener", "Gentleman", "Docent" };

        class Soup
        {
            public Vector3[] v; public int[] t; public Vector3[] n;
            public Dictionary<long, List<int>> grid = new Dictionary<long, List<int>>();
            const float Cell = 0.04f;
            static long Key(int x, int y, int z) => ((long)(x + 4096) << 40) | ((long)(y + 4096) << 20) | (long)(z + 4096);
            public Soup(Vector3[] verts, int[] tris)
            {
                v = verts; t = tris; n = new Vector3[tris.Length / 3];
                for (int i = 0; i < tris.Length; i += 3)
                {
                    var a = v[t[i]]; var b = v[t[i + 1]]; var c = v[t[i + 2]];
                    n[i / 3] = Vector3.Cross(b - a, c - a).normalized;
                    var cen = (a + b + c) / 3f;
                    long k = Key(Mathf.FloorToInt(cen.x / Cell), Mathf.FloorToInt(cen.y / Cell), Mathf.FloorToInt(cen.z / Cell));
                    if (!grid.TryGetValue(k, out var l)) grid[k] = l = new List<int>();
                    l.Add(i / 3);
                }
            }
            /// distancia con signo al triangulo mas cercano cuyo punto proyectado cae dentro (radio r); float.NaN si no hay.
            public float Signed(Vector3 p, float r)
            {
                int cx = Mathf.FloorToInt(p.x / Cell), cy = Mathf.FloorToInt(p.y / Cell), cz = Mathf.FloorToInt(p.z / Cell);
                int span = Mathf.CeilToInt(r / Cell); float best = float.MaxValue; float res = float.NaN;
                for (int x = -span; x <= span; x++) for (int y = -span; y <= span; y++) for (int z = -span; z <= span; z++)
                {
                    if (!grid.TryGetValue(Key(cx + x, cy + y, cz + z), out var l)) continue;
                    foreach (int ti in l)
                    {
                        var a = v[t[ti * 3]]; var nn = n[ti];
                        float d = Vector3.Dot(p - a, nn);
                        if (Mathf.Abs(d) >= best || Mathf.Abs(d) > r) continue;
                        var q = p - nn * d; var b = v[t[ti * 3 + 1]]; var c = v[t[ti * 3 + 2]];
                        if (Inside(q, a, b, c)) { best = Mathf.Abs(d); res = d; }
                    }
                }
                return res;
            }
            static bool Inside(Vector3 p, Vector3 a, Vector3 b, Vector3 c)
            {
                Vector3 v0 = b - a, v1 = c - a, v2 = p - a;
                float d00 = Vector3.Dot(v0, v0), d01 = Vector3.Dot(v0, v1), d11 = Vector3.Dot(v1, v1), d20 = Vector3.Dot(v2, v0), d21 = Vector3.Dot(v2, v1);
                float den = d00 * d11 - d01 * d01; if (Mathf.Abs(den) < 1e-12f) return false;
                float vv = (d11 * d20 - d01 * d21) / den, ww = (d00 * d21 - d01 * d20) / den;
                return vv >= -0.02f && ww >= -0.02f && vv + ww <= 1.02f;
            }
        }

        class Pose { public Dictionary<string, Vector3[]> verts = new Dictionary<string, Vector3[]>(); }

        static Pose Capture(GameObject inst, SkinnedMeshRenderer[] rs)
        {
            var p = new Pose();
            foreach (var r in rs)
            {
                var m = new Mesh(); r.BakeMesh(m, true);
                var v = m.vertices; var l2w = r.transform.localToWorldMatrix;
                for (int i = 0; i < v.Length; i++) v[i] = l2w.MultiplyPoint3x4(v[i]);
                p.verts[r.name] = v; Object.DestroyImmediate(m);
            }
            return p;
        }

        static bool Has(string n, string[] suf) => suf.Any(s => n.EndsWith(s));

        public static string Run(string[] folders, int walkSamples = 12)
        {
            var sb = new StringBuilder();
            var rows = new List<(float score, string text)>();
            foreach (var f in folders)
            {
                string pfPath = f == "Rose" ? "Assets/_TheLivingCanvas/Art/Models/NPC/Rose/Rose_Receptionist.fbx" : $"Assets/_TheLivingCanvas/Prefabs/NPC/NPC_{f}.prefab";
                var pf = AssetDatabase.LoadAssetAtPath<GameObject>(pfPath);
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(pf);
                inst.transform.position = new Vector3(0, -400, 0); inst.transform.rotation = Quaternion.identity;
                var an = inst.GetComponent<Animator>(); an.enabled = false;
                var rs = inst.GetComponentsInChildren<SkinnedMeshRenderer>(true);
                var low = rs.First(r => r.name.EndsWith("_Low"));
                var gar = rs.Where(r => Has(r.name, Garments)).ToArray();
                var acc = rs.Where(r => !Has(r.name, SkipAcc) && !Has(r.name, Garments)).ToArray();

                var restPose = Capture(inst, rs);
                // referencia de reposo
                var restPoke = CountPokes(restPose, low, gar);
                var restFloat = FloatMetric(restPose, low, gar, acc);
                var restEdges = new Dictionary<string, Vector3[]>(restPose.verts);

                var clips = new List<(string label, AnimationClip clip, int n)>();
                string walkAsset = Men.Contains(f) ? "Walk_Male" : "Walk_Female";
                clips.Add(("Walk", AssetDatabase.LoadAssetAtPath<AnimationClip>($"Assets/_TheLivingCanvas/Art/Animations/Gait/{walkAsset}.anim"), walkSamples));
                clips.Add(("Idle_A", Find("KayKit/KK_General.fbx", "Idle_A"), 3));
                clips.Add(("Idle_B", Find("KayKit/KK_General.fbx", "Idle_B"), 3));
                clips.Add(("Fold", AssetDatabase.LoadAssetAtPath<AnimationClip>("Assets/_TheLivingCanvas/Art/Animations/Poses/Idle_Fold_Fixed.anim"), 3));
                foreach (var (label, clip, n) in clips)
                {
                    if (clip == null) continue;
                    var worstPoke = new Dictionary<string, (int cnt, float depth, float time)>();
                    float worstFloat = 0; string worstFloatName = ""; float worstFloatT = 0;
                    var worstStretch = new Dictionary<string, (float ratio, float time)>();
                    for (int k = 0; k < n; k++)
                    {
                        float t = clip.length * k / n;
                        clip.SampleAnimation(inst, t);
                        var pose = Capture(inst, rs);
                        var pk = CountPokes(pose, low, gar);
                        foreach (var kv in pk)
                        {
                            restPoke.TryGetValue(kv.Key, out var rp);
                            int delta = kv.Value.cnt - rp.cnt;
                            if (delta > 0 && (!worstPoke.TryGetValue(kv.Key, out var w) || delta > w.cnt)) worstPoke[kv.Key] = (delta, kv.Value.depth, t);
                        }
                        var fl = FloatMetric(pose, low, gar, acc);
                        foreach (var kv in fl)
                        {
                            restFloat.TryGetValue(kv.Key, out float rf);
                            float d = kv.Value - rf;
                            if (d > worstFloat) { worstFloat = d; worstFloatName = kv.Key; worstFloatT = t; }
                        }
                        foreach (var r in rs)
                        {
                            if (r.name.EndsWith("_Eyes")) continue;
                            var tri = r.sharedMesh.triangles; var v0 = restEdges[r.name]; var v1 = pose.verts[r.name]; float mx = 0;
                            for (int i = 0; i < tri.Length; i += 3) for (int e = 0; e < 3; e++)
                            {
                                int a = tri[i + e], b = tri[i + (e + 1) % 3]; float l0 = (v0[a] - v0[b]).magnitude; if (l0 < 0.004f) continue;
                                float s = ((v1[a] - v1[b]).magnitude - 0.03f) / l0; if (s > mx) mx = s;
                            }
                            if (mx > 2.6f && (!worstStretch.TryGetValue(r.name, out var ws) || mx > ws.ratio)) worstStretch[r.name] = (mx, t);
                        }
                    }
                    foreach (var kv in worstPoke.Where(x => x.Value.cnt >= 6))
                        rows.Add((kv.Value.cnt + kv.Value.depth * 100f, $"POKE   {f,-9} {label,-6} {kv.Key,-16} +{kv.Value.cnt} verts (prof {kv.Value.depth * 1000f:F1} mm) t={kv.Value.time:F2}"));
                    if (worstFloat > 0.025f)
                        rows.Add((worstFloat * 200f, $"FLOAT  {f,-9} {label,-6} {worstFloatName,-16} +{worstFloat * 100f:F1} cm mas lejos que en reposo t={worstFloatT:F2}"));
                    foreach (var kv in worstStretch.Where(x => x.Value.ratio > 4f))
                        rows.Add((kv.Value.ratio, $"STRETCH {f,-9} {label,-6} {kv.Key,-16} x{kv.Value.ratio:F1} t={kv.Value.time:F2}"));
                }
                Object.DestroyImmediate(inst);
            }
            foreach (var r in rows.OrderByDescending(x => x.score)) sb.AppendLine(r.text);
            if (rows.Count == 0) sb.AppendLine("sin hallazgos");
            return sb.ToString();
        }

        /// diagnostico: huesos dominantes de los vertices del cuerpo que asoman por una prenda en un instante
        public static string Diagnose(string f, string clipKey, float time, string garment)
        {
            var pf = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/_TheLivingCanvas/Prefabs/NPC/NPC_{f}.prefab");
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(pf); inst.transform.position = new Vector3(0, -400, 0);
            var an = inst.GetComponent<Animator>(); an.enabled = false;
            var rs = inst.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            var low = rs.First(r => r.name.EndsWith("_Low")); var g = rs.First(r => r.name == garment);
            AnimationClip clip = clipKey.EndsWith(".anim") ? AssetDatabase.LoadAssetAtPath<AnimationClip>(clipKey) : clipKey == "Walk" ? AssetDatabase.LoadAssetAtPath<AnimationClip>($"Assets/_TheLivingCanvas/Art/Animations/Gait/{(Men.Contains(f) ? "Walk_Male" : "Walk_Female")}.anim") : Find("UAL2/UAL2_Standard.fbx", "Idle_FoldArms_Loop");
            string res;
            var rest = Capture(inst, rs); var restSoup = new Soup(rest.verts[g.name], g.sharedMesh.triangles);
            var restPoke = new HashSet<int>(); var rv = rest.verts[low.name];
            for (int i = 0; i < rv.Length; i++) { float sd = restSoup.Signed(rv[i], 0.02f); if (!float.IsNaN(sd) && sd > 0.0008f) restPoke.Add(i); }
            clip.SampleAnimation(inst, time);
            var pose = Capture(inst, rs); var soup = new Soup(pose.verts[g.name], g.sharedMesh.triangles); var bv = pose.verts[low.name];
            var m = low.sharedMesh; var bpv = m.GetBonesPerVertex(); var all = m.GetAllBoneWeights(); var start = new int[bpv.Length]; int acc = 0; for (int i = 0; i < bpv.Length; i++) { start[i] = acc; acc += bpv[i]; }
            var hist = new Dictionary<string, int>(); var heights = new List<float>();
            for (int i = 0; i < bv.Length; i++)
            {
                float sd = soup.Signed(bv[i], 0.02f);
                if (float.IsNaN(sd) || sd <= 0.0008f || restPoke.Contains(i)) continue;
                float bw = -1; int bi = 0; for (int k = 0; k < bpv[i]; k++) if (all[start[i] + k].weight > bw) { bw = all[start[i] + k].weight; bi = all[start[i] + k].boneIndex; }
                string bn = low.bones[bi].name; hist.TryGetValue(bn, out int c); hist[bn] = c + 1; heights.Add(bv[i].y - inst.transform.position.y);
            }
            res = string.Join(", ", hist.OrderByDescending(x => x.Value).Take(8).Select(x => x.Key + "=" + x.Value)) + $" | alturas {(heights.Count > 0 ? heights.Min() : 0):F2}..{(heights.Count > 0 ? heights.Max() : 0):F2}";
            Object.DestroyImmediate(inst); return res;
        }

        /// pokes de un clip concreto sobre un NPC: devuelve 'total de vertices que asoman (peor muestra, por encima del reposo)' por prenda
        public static string Test(string f, AnimationClip clip, int n)
        {
            var pf = f == "Rose" ? AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_TheLivingCanvas/Art/Models/NPC/Rose/Rose_Receptionist.fbx") : AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/_TheLivingCanvas/Prefabs/NPC/NPC_{f}.prefab");
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(pf); inst.transform.position = new Vector3(0, -400, 0);
            var an = inst.GetComponent<Animator>(); an.enabled = false;
            var rs = inst.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            var low = rs.First(r => r.name.EndsWith("_Low")); var gar = rs.Where(r => Has(r.name, Garments)).ToArray();
            var restPoke = CountPokes(Capture(inst, rs), low, gar);
            var worst = new Dictionary<string, int>();
            for (int k = 0; k < n; k++)
            {
                clip.SampleAnimation(inst, clip.length * k / n);
                foreach (var kv in CountPokes(Capture(inst, rs), low, gar)) { restPoke.TryGetValue(kv.Key, out var rp); int d = kv.Value.cnt - rp.cnt; if (d > 0 && (!worst.TryGetValue(kv.Key, out int w) || d > w)) worst[kv.Key] = d; }
            }
            Object.DestroyImmediate(inst);
            return $"{f}: total={worst.Values.Sum()} " + string.Join(" ", worst.Select(x => x.Key + "=" + x.Value));
        }

        static AnimationClip Find(string rel, string suffix)
        {
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath("Assets/_TheLivingCanvas/Art/Animations/" + rel))
            {
                var c = o as AnimationClip;
                if (c != null && !c.name.StartsWith("__preview") && c.name.EndsWith(suffix)) return c;
            }
            return null;
        }

        static Dictionary<string, (int cnt, float depth)> CountPokes(Pose pose, SkinnedMeshRenderer low, SkinnedMeshRenderer[] gar)
        {
            var res = new Dictionary<string, (int, float)>();
            var bv = pose.verts[low.name];
            foreach (var g in gar)
            {
                var soup = new Soup(pose.verts[g.name], g.sharedMesh.triangles);
                int cnt = 0; float depth = 0;
                foreach (var p in bv)
                {
                    float s = soup.Signed(p, 0.02f);
                    if (!float.IsNaN(s) && s > 0.0008f) { cnt++; if (s > depth) depth = s; }
                }
                res[g.name] = (cnt, depth);
            }
            return res;
        }

        /// percentil 95 de la distancia de los vertices de cada accesorio al cuerpo/prendas mas cercanos
        static Dictionary<string, float> FloatMetric(Pose pose, SkinnedMeshRenderer low, SkinnedMeshRenderer[] gar, SkinnedMeshRenderer[] acc)
        {
            var cloud = new List<Vector3>(pose.verts[low.name]);
            foreach (var g in gar) cloud.AddRange(pose.verts[g.name]);
            const float C = 0.06f; var grid = new Dictionary<long, List<int>>();
            System.Func<int, int, int, long> key = (x, y, z) => ((long)(x + 4096) << 40) | ((long)(y + 4096) << 20) | (long)(z + 4096);
            for (int i = 0; i < cloud.Count; i++)
            {
                var p = cloud[i]; long k = key(Mathf.FloorToInt(p.x / C), Mathf.FloorToInt(p.y / C), Mathf.FloorToInt(p.z / C));
                if (!grid.TryGetValue(k, out var l)) grid[k] = l = new List<int>(); l.Add(i);
            }
            var res = new Dictionary<string, float>();
            foreach (var a in acc)
            {
                var v = pose.verts[a.name]; var ds = new List<float>();
                foreach (var p in v)
                {
                    int cx = Mathf.FloorToInt(p.x / C), cy = Mathf.FloorToInt(p.y / C), cz = Mathf.FloorToInt(p.z / C); float best = 0.3f;
                    for (int x = -2; x <= 2; x++) for (int y = -2; y <= 2; y++) for (int z = -2; z <= 2; z++)
                        if (grid.TryGetValue(key(cx + x, cy + y, cz + z), out var l)) foreach (int i in l) { float d = (cloud[i] - p).magnitude; if (d < best) best = d; }
                    ds.Add(best);
                }
                ds.Sort(); res[a.name] = ds.Count > 0 ? ds[Mathf.Min(ds.Count - 1, Mathf.FloorToInt(ds.Count * 0.95f))] : 0f;
            }
            return res;
        }
    }
}
