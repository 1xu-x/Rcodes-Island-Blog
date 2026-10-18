param(
    [string]$BaseUrl = "https://upon-philip-suitable-reforms.trycloudflare.com",
    [string]$ApiBaseUrl = "",
    [string]$FrontendBaseUrl = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env.local"
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$ResultFile = Join-Path $RuntimeDir "verification.json"

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$settings = @{}
Get-Content -LiteralPath $EnvFile | ForEach-Object {
    if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
        $settings[$Matches[1]] = $Matches[2]
    }
}

function New-HexSecret([int]$ByteCount) {
    $bytes = New-Object byte[] $ByteCount
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    return (($bytes | ForEach-Object { $_.ToString("x2") }) -join "")
}

$suffix = Get-Date -Format "MMddHHmmss"
$username = "deploytest_$suffix"
$password = New-HexSecret 16
$otherUsername = "deployother_$suffix"
$otherPassword = New-HexSecret 16
$base = if ($ApiBaseUrl) { $ApiBaseUrl.TrimEnd("/") } else { $BaseUrl.TrimEnd("/") }
$frontendBase = if ($FrontendBaseUrl) { "$($FrontendBaseUrl.TrimEnd('/'))/" } else { "$base/" }
$results = New-Object System.Collections.ArrayList

function Add-Check([string]$Name, [bool]$Passed, [string]$Detail) {
    $item = [ordered]@{
        check = $Name
        passed = $Passed
        detail = $Detail
        time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    [void]$results.Add($item)
    $state = if ($Passed) { "PASS" } else { "FAIL" }
    Write-Host "[$state] $Name - $Detail"
}

function Invoke-JsonPost([string]$Path, $Body, $Headers) {
    $json = $Body | ConvertTo-Json -Depth 8 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $params = @{
        Uri = "$base$Path"
        Method = "Post"
        ContentType = "application/json; charset=utf-8"
        Body = $bytes
        TimeoutSec = 30
    }
    if ($Headers) { $params.Headers = $Headers }
    return Invoke-RestMethod @params
}

function Get-StatusFromError($errorRecord) {
    try {
        return [int]$errorRecord.Exception.Response.StatusCode
    } catch {
        return 0
    }
}

try {
    $html = Invoke-WebRequest -Uri $frontendBase -UseBasicParsing -TimeoutSec 30
    Add-Check "public_homepage" ($html.StatusCode -eq 200) "HTTP $($html.StatusCode), $($html.Content.Length) bytes"

    $staticImages = @(
        "images/avatar.png",
        "images/covers/default.svg",
        "images/covers/cloud-infra.jpg",
        "images/posts/deployment-flow.svg"
    )
    foreach ($imagePath in $staticImages) {
        $imageUrl = "$frontendBase$imagePath"
        $image = Invoke-WebRequest -Uri $imageUrl -UseBasicParsing -TimeoutSec 30
        Add-Check "static_image_$imagePath" ($image.StatusCode -eq 200 -and $image.RawContentLength -gt 0) "HTTP $($image.StatusCode), $($image.RawContentLength) bytes"
    }

    $health = Invoke-RestMethod -Uri "$base/api/health" -TimeoutSec 30
    Add-Check "public_api_health" ($health.status -eq "ok") "status=$($health.status)"

    $register = Invoke-JsonPost "/api/register" @{ username = $username; password = $password } $null
    Add-Check "register" ($register.username -eq $username) "user id=$($register.id), role=$($register.role)"

    $login = Invoke-RestMethod -Uri "$base/api/token" -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body @{ username = $username; password = $password } -TimeoutSec 30
    $userHeaders = @{ Authorization = "Bearer $($login.access_token)" }
    Add-Check "login" ([bool]$login.access_token) "token_type=$($login.token_type)"

    $me = Invoke-RestMethod -Uri "$base/api/users/me" -Headers $userHeaders -TimeoutSec 30
    Add-Check "authenticated_identity" ($me.username -eq $username) "username=$($me.username), role=$($me.role)"

    $posts = Invoke-RestMethod -Uri "$base/api/posts/?limit=10" -Headers $userHeaders -TimeoutSec 30
    $post = $posts.items | Select-Object -First 1
    Add-Check "post_list" ($posts.total -ge 1 -and $null -ne $post) "total=$($posts.total), first_post_id=$($post.id)"

    $detailBefore = Invoke-RestMethod -Uri "$base/api/posts/$($post.id)" -Headers $userHeaders -TimeoutSec 30
    Add-Check "post_detail" ($detailBefore.id -eq $post.id) "title=$($detailBefore.title)"

    $likeOn = Invoke-RestMethod -Uri "$base/api/posts/$($post.id)/like" -Method Post -Headers $userHeaders -TimeoutSec 30
    Add-Check "like" ($likeOn.is_liked -eq $true) "likes=$($likeOn.likes), is_liked=$($likeOn.is_liked)"

    $detailLiked = Invoke-RestMethod -Uri "$base/api/posts/$($post.id)" -Headers $userHeaders -TimeoutSec 30
    Add-Check "liked_state_readback" ($detailLiked.is_liked -eq $true) "likes=$($detailLiked.likes), is_liked=$($detailLiked.is_liked)"

    $likeOff = Invoke-RestMethod -Uri "$base/api/posts/$($post.id)/like" -Method Post -Headers $userHeaders -TimeoutSec 30
    Add-Check "unlike" ($likeOff.is_liked -eq $false) "likes=$($likeOff.likes), is_liked=$($likeOff.is_liked)"

    $likeFinal = Invoke-RestMethod -Uri "$base/api/posts/$($post.id)/like" -Method Post -Headers $userHeaders -TimeoutSec 30
    Add-Check "like_again_for_persistence" ($likeFinal.is_liked -eq $true) "likes=$($likeFinal.likes)"

    $commentText = "Deployment verification comment $suffix"
    $comment = Invoke-JsonPost "/api/posts/$($post.id)/comments/" @{ content = $commentText } $userHeaders
    Add-Check "create_comment" ($comment.content -eq $commentText) "comment id=$($comment.id)"

    $comments = Invoke-RestMethod -Uri "$base/api/posts/$($post.id)/comments/" -Headers $userHeaders -TimeoutSec 30
    $commentVisible = $comments | Where-Object { $_.id -eq $comment.id -and $_.content -eq $commentText }
    Add-Check "comment_readback" ([bool]$commentVisible) "comments=$($comments.Count)"

    $otherRegister = Invoke-JsonPost "/api/register" @{ username = $otherUsername; password = $otherPassword } $null
    $otherLogin = Invoke-RestMethod -Uri "$base/api/token" -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body @{ username = $otherUsername; password = $otherPassword } -TimeoutSec 30
    $otherHeaders = @{ Authorization = "Bearer $($otherLogin.access_token)" }
    Add-Check "second_user_register_login" ($otherRegister.username -eq $otherUsername -and [bool]$otherLogin.access_token) "user id=$($otherRegister.id)"

    $otherDeleteStatus = 0
    try {
        Invoke-RestMethod -Uri "$base/api/comments/$($comment.id)" -Method Delete -Headers $otherHeaders -TimeoutSec 30 | Out-Null
        $otherDeleteStatus = 200
    } catch {
        $otherDeleteStatus = Get-StatusFromError $_
    }
    Add-Check "other_user_cannot_delete_comment" ($otherDeleteStatus -eq 403) "HTTP $otherDeleteStatus"

    $commentB = Invoke-JsonPost "/api/posts/$($post.id)/comments/" @{ content = "Admin delete test $suffix" } $userHeaders
    $adminLogin = Invoke-RestMethod -Uri "$base/api/token" -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body @{ username = $settings["ADMIN_USERNAME"]; password = $settings["ADMIN_PASSWORD"] } -TimeoutSec 30
    $adminHeaders = @{ Authorization = "Bearer $($adminLogin.access_token)" }
    $adminMe = Invoke-RestMethod -Uri "$base/api/users/me" -Headers $adminHeaders -TimeoutSec 30
    Add-Check "admin_login" ($adminMe.role -eq "admin") "username=$($adminMe.username), role=$($adminMe.role)"

    $adminDeleteComment = Invoke-RestMethod -Uri "$base/api/comments/$($commentB.id)" -Method Delete -Headers $adminHeaders -TimeoutSec 30
    Add-Check "admin_delete_comment" ([bool]$adminDeleteComment.message) "comment id=$($commentB.id)"

    $commentC = Invoke-JsonPost "/api/posts/$($post.id)/comments/" @{ content = "Owner delete test $suffix" } $userHeaders
    $ownerDelete = Invoke-RestMethod -Uri "$base/api/comments/$($commentC.id)" -Method Delete -Headers $userHeaders -TimeoutSec 30
    Add-Check "owner_delete_comment" ([bool]$ownerDelete.message) "comment id=$($commentC.id)"

    $normalCreateStatus = 0
    try {
        Invoke-JsonPost "/api/posts/" @{
            title = "Unauthorized post $suffix"
            content = "This should be rejected"
            summary = "permission test"
            category = "Python"
            tags = ""
            cover_url = ""
        } $userHeaders | Out-Null
        $normalCreateStatus = 200
    } catch {
        $normalCreateStatus = Get-StatusFromError $_
    }
    Add-Check "normal_user_cannot_create_post" ($normalCreateStatus -eq 403) "HTTP $normalCreateStatus"

    $tempPost = Invoke-JsonPost "/api/posts/" @{
        title = "Deployment temporary post $suffix"
        content = "Temporary post used only for deployment verification."
        summary = "deployment verification"
        category = "Python"
        tags = "deployment,verification"
        cover_url = ""
    } $adminHeaders
    Add-Check "admin_create_post" ($tempPost.id -gt 0) "post id=$($tempPost.id)"

    $tempUpdate = Invoke-RestMethod -Uri "$base/api/posts/$($tempPost.id)" -Method Put `
        -Headers $adminHeaders -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes((@{
            title = "Deployment temporary post $suffix updated"
            content = "Temporary post updated during deployment verification."
            summary = "deployment verification updated"
            category = "Python"
            tags = "deployment,verification"
            cover_url = ""
        } | ConvertTo-Json -Compress))) -TimeoutSec 30
    Add-Check "admin_update_post" ($tempUpdate.title -like "*updated") "post id=$($tempUpdate.id)"

    $tempDelete = Invoke-RestMethod -Uri "$base/api/posts/$($tempPost.id)" -Method Delete -Headers $adminHeaders -TimeoutSec 30
    Add-Check "admin_delete_post" ([bool]$tempDelete.message) "post id=$($tempPost.id)"

    $summary = [ordered]@{
        base_url = $base
        frontend_base_url = $frontendBase
        verified_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        test_username = $username
        other_username = $otherUsername
        post_id = $post.id
        retained_comment_id = $comment.id
        total = $results.Count
        passed = ($results | Where-Object { $_.passed }).Count
        failed = ($results | Where-Object { -not $_.passed }).Count
        checks = $results
    }
    $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ResultFile -Encoding utf8

    Write-Host "Verification result: $($summary.passed)/$($summary.total) passed"
    if ($summary.failed -gt 0) {
        exit 1
    }
} catch {
    Add-Check "verification_aborted" $false $_.Exception.Message
    $summary = [ordered]@{
        base_url = $base
        frontend_base_url = $frontendBase
        verified_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        test_username = $username
        total = $results.Count
        passed = ($results | Where-Object { $_.passed }).Count
        failed = ($results | Where-Object { -not $_.passed }).Count
        checks = $results
    }
    $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ResultFile -Encoding utf8
    exit 1
}

