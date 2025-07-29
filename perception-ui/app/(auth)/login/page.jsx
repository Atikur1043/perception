"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { GoogleLogin } from "@react-oauth/google"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthStore } from "@/store/auth"
import { Separator } from "@/components/ui/separator"

export default function LoginPage() {
  const router = useRouter()
  const { login, loginWithGoogle } = useAuthStore()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm()

  const onSubmit = async (data) => {
    try {
      await login({ username: data.emailOrUsername, password: data.password });
      toast.success("Login successful!");
      router.push("/dashboard");
    } catch (error) {
      toast.error("Login failed. Please check your credentials.");
    }
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      await loginWithGoogle(credentialResponse.credential);
      toast.success("Google login successful!");
      router.push("/dashboard");
    } catch (error) {
      toast.error("Google login failed. Please try again.");
    }
  };

  const handleGoogleError = () => {
    toast.error("Google login was unsuccessful. Please try again.");
  };

  return (
    <div className="w-full lg:grid lg:min-h-[calc(100vh-3.5rem)] lg:grid-cols-2 xl:min-h-[calc(100vh-3.5rem)]">
      <div className="flex items-center justify-center py-12">
        <div className="mx-auto grid w-[350px] gap-6">
          <div className="grid gap-2 text-center">
            <h1 className="text-3xl font-bold">Login</h1>
            <p className="text-balance text-muted-foreground">
              Enter your username or email below to access your account
            </p>
          </div>
          <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="emailOrUsername">Username or Email</Label>
              <Input
                id="emailOrUsername"
                placeholder="m@example.com or your_username"
                {...register("emailOrUsername", { required: "This field is required" })}
              />
              {errors.emailOrUsername && <p className="text-red-500 text-xs mt-1">{errors.emailOrUsername.message}</p>}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" {...register("password", { required: "Password is required" })} />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Logging in..." : "Login"}
            </Button>
          </form>
          
          <div className="flex items-center justify-center my-4">
            <Separator className="flex-grow" />
            <span className="text-xs text-muted-foreground">OR CONTINUE WITH</span>
            <Separator className="flex-grow" />
          </div>

          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              useOneTap
            />
          </div>

          <div className="mt-4 text-center text-sm">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="underline">
              Sign up
            </Link>
          </div>
        </div>
      </div>
      <div className="hidden bg-muted lg:block">
        <img
          src="https://wallpapercave.com/wp/wp14067974.jpg"
          alt="Image"
          width="1920"
          height="1080"
          className="h-full w-full object-cover dark:brightness-[0.8]"
          onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/1920x1080/09090b/e4e4e7?text=Image+Not+Found'; }}
        />
      </div>
    </div>
  )
}
