$user = (Get-ChildItem Env:\USERNAME).Value
Write-Host "Agent username is '$user'"
Write-Host "##vso[task.setvariable variable=agent_username;]$user"
