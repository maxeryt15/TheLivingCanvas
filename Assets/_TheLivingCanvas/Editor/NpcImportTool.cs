using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Importa un NPC exportado desde Blender (Models/NPC/&lt;Folder&gt;/&lt;Folder&gt;.fbx + materials.json + Textures/NPC/&lt;Folder&gt;):
    /// avatar Humanoid, materiales TLC/Painterly por nombre, clip Idle desde la pose de reposo del avatar,
    /// controller (Idle + Walk, ver NpcWalkClipBuilder) y prefab. Mismo método que Rose.
    /// </summary>
    public static class NpcImportTool
    {
        const string Root = "Assets/_TheLivingCanvas";
        const string ModelsDir = Root + "/Art/Models/NPC";
        const string MatsDir = Root + "/Art/Materials/NPC";
        const string TexDir = Root + "/Art/Textures/NPC";
        const string PrefabDir = Root + "/Prefabs/NPC";

        public static readonly string[] Folders = { "Curator", "Guard", "Student", "Gardener", "Cafe", "Tourist", "Gentleman", "Courier", "Docent", "Painter" };

        [System.Serializable] class FlatMat { public string name; public float r, g, b, metal; public bool vc; }
        [System.Serializable] class MatData { public string folder, prefix; public FlatMat[] flat; public string[] paint; }

        [MenuItem("TheLivingCanvas/NPC/Import Batch (10)")]
        public static void ImportAll()
        {
            foreach (var f in Folders) Import(f);
            NpcWalkClipBuilder.BuildAll();
            AssetDatabase.SaveAssets();
        }

        public static string Import(string folder)
        {
            string fbx = $"{ModelsDir}/{folder}/{folder}.fbx";
            var imp = AssetImporter.GetAtPath(fbx) as ModelImporter;
            if (imp == null) return folder + ": no FBX";

            imp.animationType = ModelImporterAnimationType.Human;
            imp.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            imp.importAnimation = false;
            imp.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            imp.SaveAndReimport();

            var data = JsonUtility.FromJson<MatData>(File.ReadAllText($"{ModelsDir}/{folder}/materials.json"));
            RemapMaterials(folder, imp, data);
            imp.SaveAndReimport();

            string idlePath = $"{ModelsDir}/{folder}/{folder}_Idle.anim";
            BuildIdle(fbx, idlePath);

            string acPath = $"{ModelsDir}/{folder}/AC_{folder}.controller";
            if (AssetDatabase.LoadAssetAtPath<AnimatorController>(acPath) != null) AssetDatabase.DeleteAsset(acPath);
            var ctrl = AnimatorController.CreateAnimatorControllerAtPath(acPath);
            var idle = AssetDatabase.LoadAssetAtPath<AnimationClip>(idlePath);
            var idleState = ctrl.layers[0].stateMachine.AddState("Idle", new Vector3(200, 0, 0));
            idleState.motion = idle;
            ctrl.layers[0].stateMachine.defaultState = idleState;
            EditorUtility.SetDirty(ctrl);

            NpcWalkClipBuilder.Build(idlePath);
            MakePrefab(folder, fbx, ctrl);
            return folder + ": ok";
        }

        static void RemapMaterials(string folder, ModelImporter imp, MatData data)
        {
            string dir = $"{MatsDir}/{folder}";
            Directory.CreateDirectory(dir);
            AssetDatabase.Refresh();
            var shader = Shader.Find("TLC/Painterly");
            var flat = new Dictionary<string, FlatMat>();
            foreach (var f in data.flat) flat[f.name] = f;
            var paint = new HashSet<string>(data.paint);

            foreach (var o in AssetDatabase.LoadAllAssetsAtPath($"{ModelsDir}/{folder}/{folder}.fbx"))
            {
                var src = o as Material;
                if (src == null) continue;
                string n = src.name;
                string path = $"{dir}/M_{n}.mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
                mat.shader = shader;

                if (paint.Contains(n))
                {
                    string group = n.Substring(n.IndexOf('_') + 1);      // Cur_skin_Paint -> skin_Paint
                    group = group.Substring(0, group.IndexOf('_'));       // skin | hair | clothes
                    var tex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexDir}/{folder}/T_{data.prefix}_{group}.png");
                    mat.SetTexture("_BaseMap", tex);
                    mat.SetColor("_BaseColor", Color.white);
                    mat.SetFloat("_UseVertexColor", 0f);
                }
                else if (flat.TryGetValue(n, out var fm))
                {
                    var lin = new Color(fm.r, fm.g, fm.b, 1f);
                    mat.SetColor("_BaseColor", lin.gamma);   // el JSON es lineal; Rose usa el valor gamma
                    mat.SetFloat("_UseVertexColor", fm.vc ? 1f : 0f);
                }
                EditorUtility.SetDirty(mat);
                imp.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), n), mat);
            }
        }

        // Clip Idle: pose de reposo completa del avatar (raíz + todos los músculos) con una respiración mínima en la columna.
        static void BuildIdle(string fbxPath, string clipPath)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            try
            {
                var avatar = inst.GetComponent<Animator>().avatar;
                var handler = new HumanPoseHandler(avatar, inst.transform);
                var pose = new HumanPose();
                handler.GetHumanPose(ref pose);
                handler.Dispose();

                var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
                if (clip == null) { clip = new AnimationClip(); AssetDatabase.CreateAsset(clip, clipPath); }
                else clip.ClearCurves();
                clip.frameRate = 30f;
                const float len = 4f;

                System.Action<string, AnimationCurve> set = (prop, c) =>
                    AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve("", typeof(Animator), prop), c);
                System.Func<float, AnimationCurve> flatCurve = v => new AnimationCurve(new Keyframe(0f, v), new Keyframe(len, v));

                set("RootT.x", flatCurve(pose.bodyPosition.x));
                set("RootT.y", flatCurve(pose.bodyPosition.y));
                set("RootT.z", flatCurve(pose.bodyPosition.z));
                set("RootQ.x", flatCurve(pose.bodyRotation.x));
                set("RootQ.y", flatCurve(pose.bodyRotation.y));
                set("RootQ.z", flatCurve(pose.bodyRotation.z));
                set("RootQ.w", flatCurve(pose.bodyRotation.w));

                for (int i = 0; i < HumanTrait.MuscleCount; i++)
                {
                    string m = HumanTrait.MuscleName[i];
                    float v = pose.muscles[i];
                    if (m == "Spine Front-Back" || m == "Chest Front-Back")
                    {
                        float a = m.StartsWith("Spine") ? 0.012f : 0.008f;
                        var keys = new Keyframe[9];
                        for (int k = 0; k < 9; k++)
                            keys[k] = new Keyframe(len * k / 8f, v + a * Mathf.Sin(k / 8f * Mathf.PI * 2f));
                        var c = new AnimationCurve(keys);
                        for (int k = 0; k < c.length; k++) c.SmoothTangents(k, 0f);
                        set(m, c);
                    }
                    else set(m, flatCurve(v));
                }

                var s = AnimationUtility.GetAnimationClipSettings(clip);
                s.loopTime = true; s.startTime = 0f; s.stopTime = len;
                AnimationUtility.SetAnimationClipSettings(clip, s);
                EditorUtility.SetDirty(clip);
            }
            finally { Object.DestroyImmediate(inst); }
        }

        static void MakePrefab(string folder, string fbxPath, AnimatorController ctrl)
        {
            Directory.CreateDirectory(PrefabDir);
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath));
            inst.name = "NPC_" + folder;
            inst.GetComponent<Animator>().runtimeAnimatorController = ctrl;
            PrefabUtility.SaveAsPrefabAsset(inst, $"{PrefabDir}/NPC_{folder}.prefab");
            Object.DestroyImmediate(inst);
        }
    }
}
