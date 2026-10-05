// Détourage depuis l'original HEIC : orientation appliquée, sujet le plus haut
// retenu (une bouteille est l'objet le plus haut de la photo), recadré sur le
// sujet et réduit à une hauteur maximale. Usage : detourer2 entrée sortie.png hauteurMax
import Foundation
import Vision
import CoreImage
import ImageIO
import UniformTypeIdentifiers

let a = CommandLine.arguments
guard a.count == 4, let hMax = Double(a[3]),
      let brute = CIImage(contentsOf: URL(fileURLWithPath: a[1]), options: [.applyOrientationProperty: true]) else {
  FileHandle.standardError.write("lecture impossible\n".data(using: .utf8)!); exit(1)
}
let ctx = CIContext()
guard let image = ctx.createCGImage(brute, from: brute.extent) else { exit(1) }
let requete = VNGenerateForegroundInstanceMaskRequest()
let handler = VNImageRequestHandler(cgImage: image, options: [:])
do {
  try handler.perform([requete])
  guard let r = requete.results?.first, !r.allInstances.isEmpty else {
    FileHandle.standardError.write("aucun sujet\n".data(using: .utf8)!); exit(2)
  }
  var meilleur: CIImage? = nil
  for i in r.allInstances {
    let t = try r.generateMaskedImage(ofInstances: IndexSet(integer: i), from: handler, croppedToInstancesExtent: true)
    let ci = CIImage(cvPixelBuffer: t)
    if meilleur == nil || ci.extent.height > meilleur!.extent.height { meilleur = ci }
  }
  var sortie = meilleur!
  let echelle = min(1.0, hMax / sortie.extent.height)
  if echelle < 1.0 {
    let f = CIFilter(name: "CILanczosScaleTransform")!
    f.setValue(sortie, forKey: kCIInputImageKey)
    f.setValue(echelle, forKey: kCIInputScaleKey)
    f.setValue(1.0, forKey: kCIInputAspectRatioKey)
    sortie = f.outputImage!
  }
  guard let cg = ctx.createCGImage(sortie, from: sortie.extent),
        let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[2]) as CFURL, UTType.png.identifier as CFString, 1, nil) else { exit(3) }
  CGImageDestinationAddImage(dest, cg, nil)
  CGImageDestinationFinalize(dest)
  print("\(r.allInstances.count) \(Int(meilleur!.extent.width))x\(Int(meilleur!.extent.height))")
} catch {
  FileHandle.standardError.write("\(error)\n".data(using: .utf8)!); exit(4)
}
