import functools
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from pipeline.reader_serve import ReaderHandler


def test_media_seek_byte_ranges_and_mjs_content_type(tmp_path):
    (tmp_path / "recording.m4a").write_bytes(b"0123456789")
    (tmp_path / "app.mjs").write_text("export {};",encoding="utf-8")
    handler = functools.partial(ReaderHandler,directory=str(tmp_path))
    with ThreadingHTTPServer(("127.0.0.1",0),handler) as server:
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            for requested,body,content_range in [("bytes=3-6",b"3456","bytes 3-6/10"),("bytes=8-",b"89","bytes 8-9/10"),("bytes=-2",b"89","bytes 8-9/10")]:
                req = urllib.request.Request(url+"/recording.m4a",headers={"Range":requested})
                with urllib.request.urlopen(req) as response:
                    assert response.status == 206
                    assert response.read() == body
                    assert response.headers["Content-Range"] == content_range
            with urllib.request.urlopen(url+"/app.mjs") as response:
                assert response.headers["Content-Type"] == "text/javascript"
            req = urllib.request.Request(url+"/recording.m4a",headers={"Range":"bytes=20-30"})
            try:
                urllib.request.urlopen(req)
                assert False,"Out-of-bounds range should fail"
            except urllib.error.HTTPError as error:
                assert error.code == 416
        finally:
            server.shutdown()
            thread.join(timeout=2)
