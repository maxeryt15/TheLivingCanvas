using System;
using System.Collections.Generic;
using System.IO;
using TheLivingCanvas.Data;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Save
{
    /// <summary>Convierte pinturas a y desde <see cref="PaintingSave"/>. Las imágenes van en PNG aparte, que no cambian una vez creadas.</summary>
    public static class PaintingStore
    {
        static readonly HashSet<string> referenced = new();

        static string Folder => Path.Combine(Application.persistentDataPath, "save", "paintings");

        /// <summary>Empieza un guardado: olvida los PNG que referenciaba el anterior.</summary>
        public static void BeginSave() => referenced.Clear();

        /// <summary>Borra los PNG que ninguna pintura del guardado referencia (llamar tras escribir el JSON).</summary>
        public static void DeleteUnreferenced()
        {
            if (!Directory.Exists(Folder)) return;
            foreach (var file in Directory.GetFiles(Folder, "*.png"))
            {
                if (referenced.Contains(Path.GetFileName(file))) continue;
                try { File.Delete(file); }
                catch (Exception e) { Debug.LogWarning($"[Save] Could not delete {file}: {e.Message}"); }
            }
        }

        public static PaintingSave ToSave(PaintingItem item)
        {
            var result = item.Result;
            var save = new PaintingSave
            {
                crop = item.Crop.Id,
                variant = item.Variant?.id ?? string.Empty,
                canvasType = item.CanvasType.Id,
                style = result.Style != null ? result.Style.Id : string.Empty,
                seed = item is SeedItem,
                generation = item.Generation,
                mutation = (int)item.Mutation,
                image = WriteImage(item),
                score = result.Score,
                spill = result.Spill,
                fillShare = result.FillShare,
                quality = (int)result.Quality,
                canComeToLife = result.CanComeToLife,
                cappedByFill = result.CappedByFill
            };
            foreach (var zone in result.Zones)
            {
                int index = Array.IndexOf(item.Crop.Template.Zones, zone.Requirement);
                if (index < 0) continue;
                save.zones.Add(new ZoneSave { index = index, coverage = zone.Coverage, colorFit = zone.ColorFit, dominantColor = zone.DominantColor });
            }
            return save;
        }

        /// <summary>null (con aviso) si el cultivo o el lienzo ya no existen o falta la imagen.</summary>
        public static PaintingItem FromSave(PaintingSave save, SaveRegistry registry)
        {
            var crop = registry.FindCrop(save.crop);
            var canvasType = registry.FindCanvasType(save.canvasType);
            if (crop == null || canvasType == null) return null;

            var image = ReadImage(save.image);
            if (image == null) return null;

            CropVariant variant = null; // variante desconocida = cultivo normal
            if (!string.IsNullOrEmpty(save.variant))
                foreach (var candidate in crop.Variants)
                    if (candidate.id == save.variant) variant = candidate;

            var result = new PaintingResult
            {
                Style = string.IsNullOrEmpty(save.style) ? null : registry.FindStyle(save.style),
                Score = save.score,
                Spill = save.spill,
                FillShare = save.fillShare,
                Quality = (PaintingQuality)save.quality,
                CanComeToLife = save.canComeToLife,
                CappedByFill = save.cappedByFill
            };
            var zones = crop.Template.Zones;
            foreach (var zone in save.zones)
            {
                if (zone.index < 0 || zone.index >= zones.Length) continue;
                result.Zones.Add(new ZoneResult
                {
                    Requirement = zones[zone.index],
                    Coverage = zone.coverage,
                    ColorFit = zone.colorFit,
                    DominantColor = zone.dominantColor
                });
            }

            var mutation = (Mutation)save.mutation;
            PaintingItem item = save.seed
                ? new SeedItem(crop, variant, canvasType, result, image, save.generation, mutation)
                : new PaintingItem(crop, variant, canvasType, result, image, save.generation, mutation);
            item.ImageFile = save.image;
            referenced.Add(save.image);
            return item;
        }

        // Nombre estable: se asigna la primera vez que se guarda; el PNG solo se escribe si no existe.
        static string WriteImage(PaintingItem item)
        {
            item.ImageFile ??= Guid.NewGuid().ToString("N") + ".png";
            referenced.Add(item.ImageFile);
            try
            {
                string path = Path.Combine(Folder, item.ImageFile);
                if (!File.Exists(path))
                {
                    Directory.CreateDirectory(Folder);
                    File.WriteAllBytes(path, item.Image.EncodeToPNG());
                }
            }
            catch (Exception e) { Debug.LogException(e); }
            return item.ImageFile;
        }

        static Texture2D ReadImage(string fileName)
        {
            // Solo un nombre de archivo suelto: un save.json editado no puede apuntar fuera de la carpeta.
            bool valid = !string.IsNullOrEmpty(fileName) && Path.GetFileName(fileName) == fileName && fileName.EndsWith(".png");
            string path = valid ? Path.Combine(Folder, fileName) : null;
            try
            {
                if (path != null && File.Exists(path))
                {
                    var texture = new Texture2D(2, 2, TextureFormat.RGBA32, false)
                    {
                        name = "PaintingSnapshot",
                        wrapMode = TextureWrapMode.Clamp
                    };
                    if (texture.LoadImage(File.ReadAllBytes(path))) return texture;
                    UnityEngine.Object.Destroy(texture);
                }
            }
            catch (Exception e) { Debug.LogException(e); }
            Debug.LogWarning($"[Save] Painting image '{fileName}' is missing or unreadable; painting skipped.");
            return null;
        }
    }
}
