import Foundation
import Vision
import AppKit

// Lit le texte des étiquettes avec la reconnaissance intégrée à macOS.
for chemin in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: chemin),
          let data = img.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: data),
          let cg = bitmap.cgImage else { print("\(chemin)\t"); continue }
    let requete = VNRecognizeTextRequest()
    requete.recognitionLevel = .accurate
    requete.recognitionLanguages = ["fr-FR", "en-US"]
    requete.usesLanguageCorrection = false
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    try? handler.perform([requete])
    let mots = (requete.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    print("\(chemin)\t\(mots.joined(separator: " | "))")
}
