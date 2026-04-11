import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final ImagePicker _picker = ImagePicker();
  File? _capturedImage;

  Future<void> _captureDocument() async {
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 90,
      preferredCameraDevice: CameraDevice.rear,
    );

    if (photo != null) {
      setState(() {
        _capturedImage = File(photo.path);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan Document')),
      body: Center(
        child: _capturedImage != null
            ? Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Expanded(child: Image.file(_capturedImage!, fit: BoxFit.contain)),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      ElevatedButton.icon(
                        onPressed: _captureDocument,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Re-scan'),
                      ),
                      ElevatedButton.icon(
                        onPressed: () {
                          Navigator.of(context).pop(_capturedImage);
                        },
                        icon: const Icon(Icons.check),
                        label: const Text('Accept'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                ],
              )
            : ElevatedButton.icon(
                onPressed: _captureDocument,
                icon: const Icon(Icons.camera_alt),
                label: const Text('Capture Document'),
              ),
      ),
    );
  }
}
