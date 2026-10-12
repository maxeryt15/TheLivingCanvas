using TheLivingCanvas.Art;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Genera Prototype_Museum.unity: un rincón de museo para validar la dirección artística (ver ART_DIRECTION.md §8).
    /// Es independiente de Studio.unity y de StudioSceneBuilder. Idempotente: se puede volver a ejecutar.
    /// Menú: TheLivingCanvas/Build Art Prototype Scene. NO pisa las texturas pintadas (Art/Textures/Painted).
    /// </summary>
    public static class PrototypeMuseumBuilder
    {
        const string Root = "Assets/_TheLivingCanvas";
        const string ScenePath = Root + "/Scenes/Prototype_Museum.unity";
        const string TexFolder = Root + "/Art/Textures/Painted";
        const string MatFolder = Root + "/Art/Materials/Prototype";
        const string MeshFolder = Root + "/Art/Models/Prototype";
        const string SettingsFolder = Root + "/Settings";

        static Shader _shader;
        static Material _floor, _wall, _wood, _painting, _leaf, _petal, _stem, _pot, _center;

        // Paleta inicial de ART_DIRECTION.md
        static readonly Color Cerulean = Hex("#526A83"), Yellow = Hex("#D4A72C"), Olive = Hex("#65785A"),
                              Terracotta = Hex("#A85F47"), GreyBlue = Hex("#747983"), Cream = Hex("#E0CDB0");

        [MenuItem("TheLivingCanvas/Build Art Prototype Scene")]
        public static void Build()
        {
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;

            _shader = Shader.Find("TLC/Painterly");
            if (_shader == null) { Debug.LogError("Shader TLC/Painterly no encontrado (¿error de compilación?)."); return; }

            EnsureFolder(MatFolder); EnsureFolder(MeshFolder); EnsureFolder(SettingsFolder);
            ConfigureTextures();
            CreateMaterials();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            BuildRoom();
            BuildFrame();
            BuildPlinthAndFlower();
            BuildLighting();
            BuildCameraAndVolumes();

            EditorSceneManager.SaveScene(scene, ScenePath);
            AssetDatabase.SaveAssets();
            Debug.Log("Prototype_Museum generada: " + ScenePath);
        }

        // ---------------------------------------------------------------- texturas y materiales
        static void ConfigureTextures()
        {
            foreach (var name in new[] { "T_Wood_Floor", "T_Wall_Plaster", "T_Wood_Frame", "T_Leaf", "T_Petal", "T_Brush_Dir", "T_Painting_GreyField" })
            {
                var path = $"{TexFolder}/{name}.png";
                if (AssetImporter.GetAtPath(path) is not TextureImporter imp) { Debug.LogWarning("Falta " + path); continue; }
                imp.sRGBTexture = name != "T_Brush_Dir"; // el mapa de pincelada es un dato: 128 debe leerse como 0.5
                imp.wrapMode = name is "T_Leaf" or "T_Petal" or "T_Painting_GreyField" ? TextureWrapMode.Clamp : TextureWrapMode.Repeat;
                imp.mipmapEnabled = true;
                imp.filterMode = FilterMode.Bilinear;
                imp.anisoLevel = 8;
                imp.maxTextureSize = 2048;
                imp.textureCompression = TextureImporterCompression.CompressedHQ;
                imp.SaveAndReimport();
            }
        }

        static Texture2D Tex(string name) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexFolder}/{name}.png");

        static Material Mat(string name, Texture2D baseMap, Color tint, float brushStrength, float breakup,
                            float brushScale, bool worldBrush, bool twoSided = false)
        {
            var path = $"{MatFolder}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(_shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = _shader;
            mat.SetTexture("_BaseMap", baseMap);
            mat.SetColor("_BaseColor", tint);
            mat.SetTexture("_BrushMap", Tex("T_Brush_Dir"));
            mat.SetFloat("_BrushStrength", brushStrength);
            mat.SetFloat("_BrushBreakup", breakup);
            mat.SetFloat("_BrushScale", brushScale);
            mat.SetFloat("_BrushSpace", worldBrush ? 1f : 0f);
            mat.SetFloat("_Cull", twoSided ? 0f : 2f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static void CreateMaterials()
        {
            _floor = Mat("M_Proto_Floor", Tex("T_Wood_Floor"), Color.white, 0.18f, 0.35f, 0.8f, true);
            _wall = Mat("M_Proto_Wall", Tex("T_Wall_Plaster"), Color.white, 0.10f, 0.25f, 0.5f, true);
            _wood = Mat("M_Proto_Wood", Tex("T_Wood_Frame"), Color.white, 0.15f, 0.30f, 1.2f, true);

            _painting = Mat("M_Proto_Painting", Tex("T_Painting_GreyField"), Color.white, 0.06f, 0.0f, 1f, false);
            _painting.SetFloat("_ShadowStrength", 0.25f);   // un cuadro no debe quedar "sombreado" como un objeto
            _painting.SetFloat("_DescolorResponse", 0.6f);
            _painting.SetColor("_PreserveColor", Yellow);
            _painting.SetFloat("_PreserveRange", 0.3f);
            _painting.SetFloat("_PreserveAmount", 1f);      // el amarillo del cuadro resiste la Descoloración

            _leaf = Mat("M_Proto_Leaf", Tex("T_Leaf"), Color.white, 0.10f, 0.2f, 1f, false, true);
            _petal = Mat("M_Proto_Petal", Tex("T_Petal"), Color.white, 0.10f, 0.2f, 1f, false, true);
            _petal.SetColor("_PreserveColor", Yellow);
            _petal.SetFloat("_PreserveRange", 0.3f);
            _petal.SetFloat("_PreserveAmount", 0.7f);       // la flor 3D conserva parte de su color
            _stem = Mat("M_Proto_Stem", null, new Color(0.42f, 0.55f, 0.34f), 0.35f, 0.3f, 3f, false);
            _pot = Mat("M_Proto_Pot", null, Terracotta, 0.35f, 0.3f, 2f, false);
            _center = Mat("M_Proto_FlowerCenter", null, new Color(0.45f, 0.28f, 0.12f), 0.4f, 0.2f, 4f, false);
            foreach (var m in new[] { _leaf, _petal, _stem, _pot, _center, _floor, _wall, _wood })
                EditorUtility.SetDirty(m);
        }

        // ---------------------------------------------------------------- geometría
        static GameObject Add(string name, Mesh mesh, Material mat, Vector3 pos, Transform parent = null)
        {
            var path = $"{MeshFolder}/{mesh.name}.asset";
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(mesh, path);
            var go = new GameObject(name);
            if (parent != null) go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = mat;
            return go;
        }

        static int _seed = 100;
        static GameObject Block(string name, Transform parent, Vector3 center, Vector3 size, Material mat, float tile, int grain, float jitter = 0.006f)
            => Add(name, PrototypeMeshes.Box("Proto_" + name + "_" + _seed, size, tile, grain, _seed++, jitter), mat, center, parent);

        static void BuildRoom()
        {
            var room = new GameObject("Room").transform;
            // Suelo y paredes (esquina del museo). Cara interior de la pared del fondo: z = 3; de la izquierda: x = -2.5.
            Block("Floor", room, new Vector3(0.25f, -0.1f, 0.25f), new Vector3(5.5f, 0.2f, 5.5f), _floor, 1.6f, 0, 0.004f);
            Block("Wall_Back", room, new Vector3(0.25f, 1.6f, 3.075f), new Vector3(5.65f, 3.2f, 0.15f), _wall, 2.0f, -1, 0f);
            // Techo: así el sol solo entra por la ventana (sin él, la luz pasa por encima de las paredes).
            Block("Ceiling", room, new Vector3(0.25f, 3.275f, 0.25f), new Vector3(5.65f, 0.15f, 5.65f), _wall, 2.0f, -1, 0f);
            // Pared izquierda con una ventana (hueco z 0.5..1.8, y 0.9..2.3) por donde entra la luz.
            const float wx = -2.575f;
            Block("Wall_Left_Front", room, new Vector3(wx, 1.6f, -1.0f), new Vector3(0.15f, 3.2f, 3.0f), _wall, 2.0f, -1, 0f);
            Block("Wall_Left_Back", room, new Vector3(wx, 1.6f, 2.4f), new Vector3(0.15f, 3.2f, 1.2f), _wall, 2.0f, -1, 0f);
            Block("Wall_Left_Below", room, new Vector3(wx, 0.45f, 1.15f), new Vector3(0.15f, 0.9f, 1.3f), _wall, 2.0f, -1, 0f);
            Block("Wall_Left_Above", room, new Vector3(wx, 2.75f, 1.15f), new Vector3(0.15f, 0.9f, 1.3f), _wall, 2.0f, -1, 0f);
            Block("Window_Sill", room, new Vector3(-2.5f, 0.925f, 1.15f), new Vector3(0.3f, 0.05f, 1.45f), _wood, 0.8f, 2);
            Block("Window_Mullion", room, new Vector3(wx, 1.6f, 1.15f), new Vector3(0.05f, 1.4f, 0.05f), _wood, 0.8f, 1);
            // Zócalos (mismo material que el marco: familia "madera oscura").
            Block("Baseboard_Back", room, new Vector3(0.25f, 0.07f, 2.975f), new Vector3(5.5f, 0.14f, 0.05f), _wood, 0.8f, 0, 0.003f);
            Block("Baseboard_Left", room, new Vector3(-2.475f, 0.07f, 0.25f), new Vector3(0.05f, 0.14f, 5.5f), _wood, 0.8f, 2, 0.003f);
            // Un banco solo frente al cuadro, para contemplarlo.
            var bench = new GameObject("Bench").transform;
            bench.SetParent(room, false);
            Block("Bench_Seat", bench, new Vector3(0.15f, 0.45f, 0.9f), new Vector3(1.3f, 0.06f, 0.38f), _wood, 0.8f, 0);
            Block("Bench_Leg_L", bench, new Vector3(-0.38f, 0.21f, 0.9f), new Vector3(0.07f, 0.42f, 0.3f), _wood, 0.8f, 1);
            Block("Bench_Leg_R", bench, new Vector3(0.68f, 0.21f, 0.9f), new Vector3(0.07f, 0.42f, 0.3f), _wood, 0.8f, 1);
        }

        static void BuildFrame()
        {
            var frame = new GameObject("Painting_Frame").transform;
            frame.position = new Vector3(0f, 1.62f, 2.97f);
            const float w = 1.2f, h = 0.9f, b = 0.08f, d = 0.06f;
            Block("Frame_Top", frame, new Vector3(0, h / 2 + b / 2, 0), new Vector3(w + 2 * b, b, d), _wood, 0.8f, 0, 0.004f);
            Block("Frame_Bottom", frame, new Vector3(0, -h / 2 - b / 2, 0), new Vector3(w + 2 * b, b, d), _wood, 0.8f, 0, 0.004f);
            Block("Frame_Left", frame, new Vector3(-w / 2 - b / 2, 0, 0), new Vector3(b, h, d), _wood, 0.8f, 1, 0.004f);
            Block("Frame_Right", frame, new Vector3(w / 2 + b / 2, 0, 0), new Vector3(b, h, d), _wood, 0.8f, 1, 0.004f);
            // Lienzo ligeramente hundido; mira a -Z (hacia la sala).
            Add("Painting_Canvas", PrototypeMeshes.Quad("Proto_Canvas", w, h), _painting, new Vector3(0, 0, 0.02f), frame);
        }

        static void BuildPlinthAndFlower()
        {
            var plinth = Block("Plinth", null, new Vector3(0f, 0.23f, 2.77f), new Vector3(0.9f, 0.46f, 0.42f), _wood, 0.8f, 1);

            var profile = new[]
            {
                new Vector2(0f, 0f), new Vector2(0.07f, 0f), new Vector2(0.085f, 0.02f), new Vector2(0.10f, 0.14f),
                new Vector2(0.108f, 0.17f), new Vector2(0.098f, 0.178f), new Vector2(0.088f, 0.165f),
                new Vector2(0.088f, 0.145f), new Vector2(0f, 0.145f),
            };
            var pot = Add("Pot", PrototypeMeshes.Lathe("Proto_Pot", profile, 28, 0.5f), _pot, new Vector3(0f, 0.46f, 2.77f));
            pot.transform.SetParent(plinth.transform, true);
            BuildFlower(pot.transform);
        }

        static Vector3 StemPoint(float t)
        {
            // Bézier cúbica suave, ligeramente arqueada hacia el espectador.
            var p0 = Vector3.zero; var p1 = new Vector3(0f, 0.16f, -0.05f);
            var p2 = new Vector3(0f, 0.30f, 0.05f); var p3 = new Vector3(0f, 0.42f, 0.02f);
            var u = 1 - t;
            return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3;
        }

        static void BuildFlower(Transform pot)
        {
            var flower = new GameObject("Flower").transform;
            flower.SetParent(pot, false);
            flower.localPosition = new Vector3(0f, 0.145f, 0f);

            Add("Stem", PrototypeMeshes.Tube("Proto_Stem", StemPoint, 0.011f, 0.007f, 18, 8), _stem, Vector3.zero, flower);

            // Hojas: siluetas reconocibles, caídas hacia fuera.
            var leafMesh = PrototypeMeshes.Blade("Proto_Leaf", PrototypeMeshes.LeafL, PrototypeMeshes.LeafHalf, PrototypeMeshes.LeafA, PrototypeMeshes.LeafB, -0.9f, 0.5f);
            AssetDatabase.DeleteAsset($"{MeshFolder}/{leafMesh.name}.asset");
            AssetDatabase.CreateAsset(leafMesh, $"{MeshFolder}/{leafMesh.name}.asset");
            AddLeaf(flower, leafMesh, 0.28f, 70f, 0.75f, 62f);
            AddLeaf(flower, leafMesh, 0.45f, -115f, 0.6f, 55f);

            // Cabeza de la flor: ligeramente inclinada hacia el espectador (-Z).
            var head = new GameObject("Head").transform;
            head.SetParent(flower, false);
            head.localPosition = StemPoint(1f);
            head.localRotation = Quaternion.Euler(-32f, 0f, 0f);

            var dome = new[] { new Vector2(0f, 0f), new Vector2(0.024f, 0.002f), new Vector2(0.026f, 0.01f), new Vector2(0.016f, 0.02f), new Vector2(0f, 0.024f) };
            Add("Center", PrototypeMeshes.Lathe("Proto_Center", dome, 18, 0.1f), _center, new Vector3(0f, -0.004f, 0f), head);

            var petalMesh = PrototypeMeshes.Blade("Proto_Petal", PrototypeMeshes.PetalL, PrototypeMeshes.PetalHalf, PrototypeMeshes.PetalA, PrototypeMeshes.PetalB, 0.55f, 0.35f);
            AssetDatabase.DeleteAsset($"{MeshFolder}/{petalMesh.name}.asset");
            AssetDatabase.CreateAsset(petalMesh, $"{MeshFolder}/{petalMesh.name}.asset");
            var rng = new System.Random(7);
            AddPetalRing(head, petalMesh, 9, 74f, 0.62f, 0f, rng);
            AddPetalRing(head, petalMesh, 7, 48f, 0.48f, 20f, rng);
        }

        static void AddLeaf(Transform flower, Mesh mesh, float t, float yaw, float scale, float tilt)
        {
            var go = new GameObject("Leaf");
            go.transform.SetParent(flower, false);
            go.transform.localPosition = StemPoint(t);
            go.transform.localRotation = Quaternion.Euler(0f, yaw, 0f) * Quaternion.Euler(-tilt, 0f, 0f);
            go.transform.localScale = Vector3.one * scale;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = _leaf;
        }

        static void AddPetalRing(Transform head, Mesh mesh, int count, float tilt, float scale, float yawOffset, System.Random rng)
        {
            for (var i = 0; i < count; i++)
            {
                var j = (float)(rng.NextDouble() * 2 - 1);
                var go = new GameObject("Petal");
                go.transform.SetParent(head, false);
                go.transform.localPosition = new Vector3(0f, 0.002f, 0f);
                go.transform.localRotation = Quaternion.Euler(0f, yawOffset + i * 360f / count + j * 6f, 0f) * Quaternion.Euler(-(tilt + j * 5f), 0f, 0f);
                go.transform.localScale = Vector3.one * (scale * (1f + j * 0.08f));
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                go.AddComponent<MeshRenderer>().sharedMaterial = _petal;
            }
        }

        // ---------------------------------------------------------------- luz, cámara, volúmenes
        static void BuildLighting()
        {
            // Luz de ventana: pálida, entra por la izquierda y cae hacia el cuadro y la flor.
            var sunGo = new GameObject("Window Light");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.93f, 0.80f);
            sun.intensity = 1.5f;
            sun.shadows = LightShadows.Soft;
            sun.shadowStrength = 0.9f;
            sunGo.transform.rotation = Quaternion.Euler(50f, 90f, 0f);
            RenderSettings.sun = sun;

            // Foco cálido discreto sobre el cuadro: pequeña "esperanza" sin brillo mágico.
            var spotGo = new GameObject("Painting Spot");
            var spot = spotGo.AddComponent<Light>();
            spot.type = LightType.Spot;
            spot.color = new Color(1f, 0.88f, 0.68f);
            spot.intensity = 4.5f;
            spot.range = 6f;
            spot.spotAngle = 85f;
            spot.innerSpotAngle = 15f;
            spot.shadows = LightShadows.None;
            spotGo.transform.position = new Vector3(0f, 3.0f, 0.9f);
            spotGo.transform.rotation = Quaternion.LookRotation(new Vector3(0f, 1.62f, 2.97f) - spotGo.transform.position);

            // Ambiente: cielo azulado, ecuador gris, suelo cálido tenue (nada de skybox por defecto).
            RenderSettings.skybox = null;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.52f, 0.60f, 0.70f);
            RenderSettings.ambientEquatorColor = new Color(0.44f, 0.45f, 0.49f);
            RenderSettings.ambientGroundColor = new Color(0.28f, 0.21f, 0.17f);
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = 0.03f;
            RenderSettings.fogColor = new Color(0.50f, 0.55f, 0.62f);
        }

        static void BuildCameraAndVolumes()
        {
            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 50f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.33f, 0.37f, 0.43f);
            camGo.AddComponent<AudioListener>();
            camGo.AddComponent<UniversalAdditionalCameraData>().renderPostProcessing = true;
            camGo.transform.position = new Vector3(2.1f, 1.5f, -1.7f);
            camGo.transform.rotation = Quaternion.LookRotation(new Vector3(-0.3f, 1.2f, 2.6f) - camGo.transform.position);

            var baseGo = new GameObject("Base Volume");
            var baseVol = baseGo.AddComponent<Volume>();
            baseVol.isGlobal = true;
            baseVol.sharedProfile = CreateProfile("PrototypeBaseProfile", false);

            var descGo = new GameObject("Descolor Atmosphere");
            var descVol = descGo.AddComponent<Volume>();
            descVol.isGlobal = true;
            descVol.priority = 10f;
            descVol.weight = 0f;
            descVol.sharedProfile = CreateProfile("PrototypeDescolorProfile", true);

            var ctrl = new GameObject("Descoloration Controller").AddComponent<PainterlyDescolor>();
            ctrl.atmosphere = descVol;
            camGo.AddComponent<PrototypeViewer>().descolor = ctrl;
        }

        static VolumeProfile CreateProfile(string name, bool descolor)
        {
            var path = $"{SettingsFolder}/{name}.asset";
            AssetDatabase.DeleteAsset(path);
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, path);

            var tone = Override<Tonemapping>(profile);
            tone.mode.Override(TonemappingMode.Neutral);

            if (!descolor)
            {
                // Bloom casi apagado: no queremos que la luz borre las pinceladas.
                var bloom = Override<Bloom>(profile);
                bloom.intensity.Override(0.12f);
                bloom.threshold.Override(1.2f);
                bloom.scatter.Override(0.6f);
                var vignette = Override<Vignette>(profile);
                vignette.intensity.Override(0.22f);
                vignette.smoothness.Override(0.5f);
                var wb = Override<WhiteBalance>(profile);
                wb.temperature.Override(6f);
            }
            else
            {
                // Descoloración: menos saturación, más frío y algo más de contraste; sin llegar a gris.
                var adj = Override<ColorAdjustments>(profile);
                adj.saturation.Override(-20f);
                adj.contrast.Override(8f);
                var wb = Override<WhiteBalance>(profile);
                wb.temperature.Override(-8f);
                var split = Override<SplitToning>(profile);
                split.shadows.Override(new Color(0.44f, 0.48f, 0.57f));
                split.highlights.Override(new Color(0.72f, 0.68f, 0.60f));
                split.balance.Override(-10f);
                var vignette = Override<Vignette>(profile);
                vignette.intensity.Override(0.32f);
            }
            EditorUtility.SetDirty(profile);
            return profile;
        }

        static T Override<T>(VolumeProfile profile) where T : VolumeComponent
        {
            var component = profile.Add<T>(true);
            component.hideFlags = HideFlags.HideInInspector | HideFlags.HideInHierarchy;
            AssetDatabase.AddObjectToAsset(component, profile);
            return component;
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            var parent = System.IO.Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, System.IO.Path.GetFileName(path));
        }

        static Color Hex(string hex) { ColorUtility.TryParseHtmlString(hex, out var c); return c; }
    }
}
