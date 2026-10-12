using System;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Cruce de un cultivo: si su compañero crece cerca al cosechar, la polinización puede enseñar el boceto del híbrido.</summary>
    [Serializable]
    public class CropCross
    {
        public CropDefinition partner;
        public CropDefinition hybrid;
    }
}
