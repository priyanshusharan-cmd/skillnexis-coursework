import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class Post {
  const Post(this.id, this.title, this.body);
  final int id;
  final String title;
  final String body;
}

/// Assignment 1: fetch and display data from a public API (JSONPlaceholder, no key needed).
Future<List<Post>> fetchPosts(http.Client client) async {
  final res = await client.get(Uri.https('jsonplaceholder.typicode.com', '/posts', {'_limit': '20'}));
  if (res.statusCode != 200) throw Exception('Server returned ${res.statusCode}');
  return [
    for (final p in jsonDecode(res.body) as List<dynamic>)
      Post((p as Map<String, dynamic>)['id'] as int, p['title'] as String, p['body'] as String),
  ];
}

class PostsScreen extends StatefulWidget {
  const PostsScreen({super.key, required this.client});
  final http.Client client;

  @override
  State<PostsScreen> createState() => _PostsScreenState();
}

class _PostsScreenState extends State<PostsScreen> {
  late Future<List<Post>> _posts = fetchPosts(widget.client);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Public API: posts')),
      body: FutureBuilder<List<Post>>(
        future: _posts,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snap.hasError) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Text('Could not load posts.'),
                TextButton(onPressed: () => setState(() => _posts = fetchPosts(widget.client)), child: const Text('Retry')),
              ]),
            );
          }
          return ListView(children: [
            for (final p in snap.data!) ListTile(leading: CircleAvatar(child: Text('${p.id}')), title: Text(p.title), subtitle: Text(p.body, maxLines: 2, overflow: TextOverflow.ellipsis)),
          ]);
        },
      ),
    );
  }
}
