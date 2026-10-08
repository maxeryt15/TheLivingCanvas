using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Genera la escena Studio (vertical slice) con placeholders: suelo, paredes,
    /// luz cálida, cámara y post-processing. Es idempotente: se puede volver a ejecutar.
    /// Menú: TheLivingCanvas/Build Studio Scene. Batchmode: -executeMethod TheLivingCanvas.EditorTools.StudioSceneBuilder.Build
    /// </summary>
    public static class StudioSceneBuilder
    {
        const string Root = "Assets/_TheLivingCanvas";
        const string ScenePath = Root + "/Scenes/Studio.unity";
        const string MaterialsFolder = Root + "/Art/Materials";
        const string ProfilePath = Root + "/Settings/StudioVolumeProfile.asset";

        [MenuItem("TheLivingCanvas/Build Studio Scene")]
        public static void Build()
        {
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                return;

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var floorMat = GetOrCreateMaterial("M_Floor_Wood", new Color(0.55f, 0.38f, 0.24f));
            var wallMat = GetOrCreateMaterial("M_Wall_Cream", new Color(0.93f, 0.87f, 0.76f));
            var accentMat = GetOrCreateMaterial("M_Accent_Terracotta", new Color(0.80f, 0.45f, 0.30f));

            // Entorno: un estudio abierto por dos lados para que la cámara en 3ª persona vea bien.
            var environment = new GameObject("Environment");
            CreateBlock("Floor", environment.transform, new Vector3(0f, -0.1f, 0f), new Vector3(12f, 0.2f, 12f), floorMat);
            CreateBlock("Wall_Back", environment.transform, new Vector3(0f, 1.5f, 6f), new Vector3(12f, 3f, 0.2f), wallMat);
            CreateBlock("Wall_Left", environment.transform, new Vector3(-6f, 1.5f, 0f), new Vector3(0.2f, 3f, 12f), wallMat);
            CreateBlock("Table", environment.transform, new Vector3(-4.5f, 0.4f, 4.5f), new Vector3(2f, 0.8f, 1f), accentMat);

            // Luz cálida de media tarde.
            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.88f, 0.72f);
            sun.intensity = 1.6f;
            sun.shadows = LightShadows.Soft;
            sunGo.transform.rotation = Quaternion.Euler(40f, -35f, 0f);

            RenderSettings.sun = sun;
            RenderSettings.skybox = AssetDatabase.GetBuiltinExtraResource<Material>("Default-Skybox.mat");
            RenderSettings.ambientMode = AmbientMode.Skybox;

            // Cámara provisional (en la Fase 1B la reemplaza Cinemachine).
            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            camGo.AddComponent<AudioListener>();
            camGo.AddComponent<UniversalAdditionalCameraData>().renderPostProcessing = true;
            cam.transform.position = new Vector3(3f, 5f, -8f);
            cam.transform.LookAt(new Vector3(-1f, 0.5f, 1.5f));

            var volumeGo = new GameObject("Global Volume");
            var volume = volumeGo.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = CreateVolumeProfile();

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            Debug.Log($"[StudioSceneBuilder] Escena generada en {ScenePath}");
        }

        static GameObject CreateBlock(string name, Transform parent, Vector3 position, Vector3 scale, Material material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent);
            go.transform.localPosition = position;
            go.transform.localScale = scale;
            go.GetComponent<MeshRenderer>().sharedMaterial = material;
            go.isStatic = true;
            return go;
        }

        static Material GetOrCreateMaterial(string name, Color color)
        {
            var path = $"{MaterialsFolder}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null)
            {
                mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.SetColor("_BaseColor", color);
            mat.SetFloat("_Smoothness", 0.15f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static VolumeProfile CreateVolumeProfile()
        {
            AssetDatabase.DeleteAsset(ProfilePath);
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, ProfilePath);

            var bloom = AddOverride<Bloom>(profile);
            bloom.intensity.Override(0.4f);
            bloom.threshold.Override(1f);
            bloom.scatter.Override(0.7f);

            var tonemapping = AddOverride<Tonemapping>(profile);
            tonemapping.mode.Override(TonemappingMode.Neutral);

            var whiteBalance = AddOverride<WhiteBalance>(profile);
            whiteBalance.temperature.Override(12f);

            var colorAdjustments = AddOverride<ColorAdjustments>(profile);
            colorAdjustments.saturation.Override(10f);
            colorAdjustments.contrast.Override(5f);

            var vignette = AddOverride<Vignette>(profile);
            vignette.intensity.Override(0.2f);

            EditorUtility.SetDirty(profile);
            return profile;
        }

        static T AddOverride<T>(VolumeProfile profile) where T : VolumeComponent
        {
            var component = profile.Add<T>(true);
            component.hideFlags = HideFlags.HideInInspector | HideFlags.HideInHierarchy;
            AssetDatabase.AddObjectToAsset(component, profile);
            return component;
        }
    }
}
