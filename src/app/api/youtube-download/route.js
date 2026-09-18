import { NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { AIService } from "@/lib/services/ai";

export async function POST(req) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await req.json();
    const { video_url, format } = body;

    if (!video_url) {
      return NextResponse.json({ error: "YouTube video URL is required" }, { status: 400 });
    }

    const headerApiKey = req.headers.get("x-custom-api-key");
    const customApiKey = headerApiKey || body.customApiKey || session.user.customApiKey || null;

    const result = await AIService.youtubeDownload(session.user.id, {
      video_url,
      format: format || "720",
      customApiKey,
    });

    return NextResponse.json(result);
  } catch (error) {
    if (error.message === "Insufficient credits") {
      return new NextResponse("Insufficient credits", { status: 403 });
    }
    console.error("[YOUTUBE_DOWNLOAD]", error);
    return new NextResponse(error.message || "Internal Error", { status: 500 });
  }
}
