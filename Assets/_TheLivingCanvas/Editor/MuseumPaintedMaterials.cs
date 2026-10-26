using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Crea materiales URP Lit con las texturas pintadas (Van Gogh) y los asigna por nombre a los FBX del museo
    /// (remap del importer). Datos: Museum_Int_Painted.json / Museum_Ext_Painted.json (exportados desde Blender).
    /// </summary>
    public static class MuseumPaintedMaterials
    {
        const string ModelDir = "Assets/_TheLivingCanvas/Art/Models/Museum";
        const string MatDir = "Assets/_TheLivingCanvas/Art/Materials/Museum/Painted";
        const string TexDir = "Assets/_TheLivingCanvas/Art/Textures/Painted/Museum";

        [System.Serializable] class Entry { public string tex; public float scale = 1f; public float[] tint; public float rough = 1f; public float metal; }

        [MenuItem("TheLivingCanvas/Museum/Apply Painted Materials")]
        public static void ApplyAll()
        {
            Apply("Int");
            Apply("Ext");
            AssetDatabase.SaveAssets();
        }

        static void Apply(string tag)
        {
            var jsonPath = $"{ModelDir}/Museum_{tag}_Painted.json";
            if (!File.Exists(jsonPath)) return;
            var entries = ParseEntries(File.ReadAllText(jsonPath));
            if (!AssetDatabase.IsValidFolder(MatDir)) Directory.CreateDirectory(MatDir);

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var mats = new Dictionary<string, Material>();
            foreach (var kv in entries)
            {
                var e = kv.Value;
                string path = $"{MatDir}/{tag}_{kv.Key}.mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexDir}/{e.tex}");
                mat.SetTexture("_BaseMap", tex);
                mat.SetTextureScale("_BaseMap", new Vector2(e.scale, e.scale));
                var lin = new Color(e.tint[0], e.tint[1], e.tint[2], 1f);
                mat.SetColor("_BaseColor", lin.gamma);   // el JSON viene en lineal; la propiedad de color espera gamma
                mat.SetFloat("_Smoothness", 1f - e.rough);
                mat.SetFloat("_Metallic", e.metal);
                EditorUtility.SetDirty(mat);
                mats[kv.Key] = mat;
            }

            foreach (var fbx in Directory.GetFiles(ModelDir, $"Museum_{tag}_*.fbx"))
            {
                var p = fbx.Replace('\\', '/');
                var imp = AssetImporter.GetAtPath(p) as ModelImporter;
                if (imp == null) continue;
                foreach (var kv in mats)
                    imp.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), kv.Key), kv.Value);
                imp.SaveAndReimport();
            }
        }

        // JsonUtility no lee diccionarios: se envuelve el objeto raíz en una lista de pares.
        static Dictionary<string, Entry> ParseEntries(string json)
        {
            var result = new Dictionary<string, Entry>();
            var root = MiniJson.Parse(json) as Dictionary<string, object>;
            foreach (var kv in root)
            {
                var d = (Dictionary<string, object>)kv.Value;
                var e = new Entry
                {
                    tex = (string)d["tex"],
                    scale = System.Convert.ToSingle(d["scale"]),
                    rough = System.Convert.ToSingle(d["rough"]),
                    metal = System.Convert.ToSingle(d["metal"]),
                };
                var t = (List<object>)d["tint"];
                e.tint = new[] { System.Convert.ToSingle(t[0]), System.Convert.ToSingle(t[1]), System.Convert.ToSingle(t[2]) };
                result[kv.Key] = e;
            }
            return result;
        }
    }

    /// <summary>Lector JSON mínimo (objetos, listas, cadenas, números) para no depender de paquetes.</summary>
    static class MiniJson
    {
        public static object Parse(string s) { int i = 0; return Value(s, ref i); }

        static void Ws(string s, ref int i) { while (i < s.Length && char.IsWhiteSpace(s[i])) i++; }

        static object Value(string s, ref int i)
        {
            Ws(s, ref i);
            char c = s[i];
            if (c == '{')
            {
                var d = new Dictionary<string, object>(); i++;
                Ws(s, ref i);
                if (s[i] == '}') { i++; return d; }
                while (true)
                {
                    Ws(s, ref i); string k = Str(s, ref i); Ws(s, ref i); i++; // ':'
                    d[k] = Value(s, ref i); Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    i++; return d;
                }
            }
            if (c == '[')
            {
                var l = new List<object>(); i++;
                Ws(s, ref i);
                if (s[i] == ']') { i++; return l; }
                while (true)
                {
                    l.Add(Value(s, ref i)); Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    i++; return l;
                }
            }
            if (c == '"') return Str(s, ref i);
            int st = i;
            while (i < s.Length && ",]} \r\n\t".IndexOf(s[i]) < 0) i++;
            string tok = s.Substring(st, i - st);
            if (tok == "null") return null;
            return double.Parse(tok, System.Globalization.CultureInfo.InvariantCulture);
        }

        static string Str(string s, ref int i)
        {
            i++; int st = i;
            while (s[i] != '"') i++;
            var r = s.Substring(st, i - st); i++; return r;
        }
    }
}
