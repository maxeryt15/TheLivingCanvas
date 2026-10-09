using System.Collections.Generic;
using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>Cultivos que el jugador sabe pintar. Se empieza con el girasol; el resto se compra en la tienda.</summary>
    public class Sketchbook : MonoBehaviour
    {
        [SerializeField] List<CropDefinition> knownCrops = new();

        public IReadOnlyList<CropDefinition> KnownCrops => knownCrops;

        public bool Knows(CropDefinition crop) => knownCrops.Contains(crop);

        /// <summary>Aprende un cultivo nuevo (false si ya lo sabía).</summary>
        public bool Learn(CropDefinition crop)
        {
            if (crop == null || knownCrops.Contains(crop)) return false;
            knownCrops.Add(crop);
            return true;
        }
    }
}
