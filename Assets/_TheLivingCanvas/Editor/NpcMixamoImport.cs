using System.IO;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Configura los FBX de animacion (Mixamo) de Art/Animations/Mixamo como Humanoid: un clip por archivo con el nombre del archivo, en bucle
    /// y en su sitio (raiz horizontal/rotacion/altura bloqueadas en la pose), para poder reproducirlos en cualquier NPC Humanoid.
    /// </summary>
    public static class NpcMixamoImport
    {
        public const string Dir = "Assets/_TheLivingCanvas/Art/Animations/Mixamo";

        public static string SetupAll()
        {
            int n = 0; var sb = new System.Text.StringBuilder();
            foreach (var path in Directory.GetFiles(Dir, "*.fbx"))
            {
                string p = path.Replace('\\', '/');
                var imp = AssetImporter.GetAtPath(p) as ModelImporter;
                if (imp == null) { sb.AppendLine("sin importer: " + p); continue; }
                string name = Path.GetFileNameWithoutExtension(p);
                imp.animationType = ModelImporterAnimationType.Human;
                imp.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                imp.importAnimation = true;
                imp.materialImportMode = ModelImporterMaterialImportMode.None;
                imp.importBlendShapes = false; imp.importCameras = false; imp.importLights = false;
                // el clip original (normalmente 'mixamo.com') se renombra y se configura
                var clips = imp.defaultClipAnimations;
                if (clips.Length == 0) { sb.AppendLine("sin clips: " + name); continue; }
                var c = clips[0];
                c.name = name; c.loopTime = true; c.loopPose = false;
                c.lockRootRotation = true; c.lockRootHeightY = true; c.lockRootPositionXZ = true;
                c.keepOriginalOrientation = true; c.keepOriginalPositionY = true; c.keepOriginalPositionXZ = true;
                imp.clipAnimations = new[] { c };
                imp.SaveAndReimport();
                n++;
            }
            return n + " FBX configurados\n" + sb;
        }
    }
}
