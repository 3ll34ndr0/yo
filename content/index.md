---
title: ""
---

<div class="home-grid">

<div class="home-main">

<article class="panel panel-projects">
<header><strong>Projects</strong></header>
{{< shell "python3 scripts/projects_list.py" >}}
</article>

<article class="panel panel-activity">
<header><strong>GitHub activity</strong></header>
{{< shell "python3 scripts/contributions.py 3ll34ndr0" >}}
</article>

<article class="panel panel-usage">
<header><strong>Claude Code usage</strong></header>
{{< shell "python3 scripts/claude_usage.py render" >}}
</article>

</div>

<div class="home-side">

<article class="panel panel-contact">
<header><strong>Contact</strong></header>
<ul class="contact-list">
<li>✉️ <a href="mailto:elleandro@gmail.com">elleandro@gmail.com</a></li>
<li>📍 Argentina</li>
</ul>
<p><a href="/cv.pdf" role="button" class="primary" download>⬇ Download CV (PDF)</a></p>
<ul class="profile-links">
<li><a href="https://github.com/3ll34ndr0">GitHub</a></li>
<li><a href="https://www.linkedin.com/in/leandromarso/">LinkedIn</a></li>
</ul>
</article>

<article class="panel panel-posts">
<header><strong>Posts</strong></header>
{{< shell "python3 scripts/posts_list.py --limit 5" >}}
</article>

</div>

</div>
