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

  Future<void> _captureDocument({ImageSource source = ImageSource.camera}) async {
    final XFile? photo = await _picker.pickImage(
      source: source,
      imageQuality: 90,
      preferredCameraDevice: CameraDevice.rear,
    );

    if (photo != null) {
      setState(() {
        _capturedImage = File(photo.path);
      });
    }
  }

  void _showSourcePicker() {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Chụp ảnh'),
              onTap: () {
                Navigator.pop(ctx);
                _captureDocument(source: ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Chọn từ thư viện'),
              onTap: () {
                Navigator.pop(ctx);
                _captureDocument(source: ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
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
                        onPressed: _showSourcePicker,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Chụp lại'),
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
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton.icon(
                    onPressed: () => _captureDocument(source: ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Chụp ảnh'),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: () => _captureDocument(source: ImageSource.gallery),
                    icon: const Icon(Icons.photo_library),
                    label: const Text('Chọn từ thư viện'),
                  ),
                ],
              ),
      ),
    );
  }
}
